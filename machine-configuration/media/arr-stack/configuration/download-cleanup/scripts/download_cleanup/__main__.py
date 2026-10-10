import logging
import os
import sys
import threading
import xml.etree.ElementTree as ElementTree
from http.server import HTTPServer
from pathlib import Path

from .bootstrap import bootstrap
from .clients import JellyfinClient, MediaClient, TorrentClient
from .filesystem import Filesystem
from .ledger import Ledger
from .server import webhook_handler
from .worker import CleanupWorker


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    stack_home = Path(os.environ["ARR_CLEANUP_STACK_HOME"])
    bind_address = next(
        line.split("=", 1)[1].strip()
        for line in (stack_home / ".env").read_text().splitlines()
        if line.startswith("ARR_BIND_ADDR=")
    )
    credentials = Path(os.environ["CREDENTIALS_DIRECTORY"])
    password = (credentials / "qbittorrent-password").read_text().strip()
    if not password:
        raise RuntimeError("cleanup password is empty")
    ledger = Ledger(Path(os.environ["STATE_DIRECTORY"]) / "cleanup.sqlite")
    media_clients = {
        app: MediaClient(
            f"http://{bind_address}:{port}/api/v3",
            ElementTree.parse(stack_home / f"config/{app}/config.xml").findtext(
                "ApiKey"
            ),
            app,
        )
        for app, port in (("radarr", 7878), ("sonarr", 8989))
    }
    torrents = TorrentClient(f"http://{bind_address}:8080", "admin", password)
    filesystem = Filesystem(stack_home / "data")
    if sys.argv[1:] == ["bootstrap"]:
        bootstrap(ledger, media_clients, torrents, filesystem)
        return
    jellyfin = JellyfinClient(
        "http://127.0.0.1:8096", (credentials / "jellyfin-api-key").read_text().strip()
    )
    worker = CleanupWorker(ledger, media_clients, torrents, filesystem, jellyfin)
    wake_worker = threading.Event()

    def run_worker():
        try:
            while True:
                wake_worker.clear()
                worker.run_pending()
                wake_worker.wait(30)
        except Exception:
            logging.exception("Cleanup worker failed")
            os._exit(1)

    threading.Thread(target=run_worker, daemon=True).start()
    server = HTTPServer(
        ("172.28.0.1", 8789), webhook_handler(ledger, password, wake_worker)
    )
    logging.info("Listening for native Radarr/Sonarr lifecycle webhooks")
    server.serve_forever()


if __name__ == "__main__":
    main()
