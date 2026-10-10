import base64
import hmac
import json
import logging
from http.server import BaseHTTPRequestHandler

from .domain import parse_event


def webhook_handler(ledger, password, wake_worker):
    authorization = "Basic " + base64.b64encode(f"cleanup:{password}".encode()).decode()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def reply(self, status):
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self):
            if not hmac.compare_digest(
                self.headers.get("Authorization", "").encode(), authorization.encode()
            ):
                self.reply(401)
                return
            app = self.path.removeprefix("/")
            if app not in ("radarr", "sonarr"):
                self.reply(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 512 * 1024:
                    self.reply(413)
                    return
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("webhook must be an object")
                event = parse_event(app, payload)
                if event is not None:
                    if event.kind == "download":
                        ledger.record_download(event.media, event.download_hash)
                    else:
                        ledger.enqueue(event.media)
                        logging.info("Queued cleanup for %s/%s", app, event.media.title)
                    wake_worker.set()
            except (KeyError, TypeError, ValueError):
                self.reply(400)
                return
            except Exception:
                logging.exception("Could not persist %s webhook", app)
                self.reply(503)
                return
            self.reply(200)

        def log_message(self, format, *arguments):
            logging.info("Webhook %s", format % arguments)

    return Handler
