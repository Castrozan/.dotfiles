"""Reconcile audiobook services using APIs; secrets are read only at runtime."""

import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from api_client import ApiError, Client
from audiobookshelf import provision_abs
from indexers import select_indexers
from readmeabook import provision_rmab


def main():
    os.umask(0o077)
    credentials = {
        "username": os.environ["AUDIOBOOK_USERNAME"],
        "password": Path(os.environ["AUDIOBOOK_PASSWORD_FILE"]).read_text().strip(),
    }
    if not credentials["password"]:
        raise RuntimeError("Audiobook password secret is empty")
    key = ET.parse(os.environ["PROWLARR_CONFIG_FILE"]).findtext("ApiKey")
    if not key:
        raise RuntimeError("Prowlarr API key missing")
    prowlarr = Client(os.environ["PROWLARR_BASE_URL"], {"X-Api-Key": key})
    indexers = select_indexers(prowlarr.ready("/api/v1/indexer"))
    library_id, token = provision_abs(
        Client(os.environ["AUDIOBOOKSHELF_BASE_URL"]),
        credentials,
        Path(os.environ.get("STATE_DIRECTORY", "/var/lib/arr-audiobooks"))
        / "audiobookshelf-api-token",
    )
    provision_rmab(
        Client(os.environ["READMEABOOK_BASE_URL"]),
        credentials,
        library_id,
        token,
        key,
        indexers,
        os.environ["QBITTORRENT_USERNAME"],
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            str(error)
            if isinstance(error, (ApiError, RuntimeError))
            else f"Provisioning failed: {type(error).__name__}",
            file=sys.stderr,
        )
        sys.exit(1)
