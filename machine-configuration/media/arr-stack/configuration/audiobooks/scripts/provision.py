"""Reconcile audiobook services using APIs; secrets are read only at runtime."""

import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from readmeabook import AUDIOBOOK_DIRECTORY, provision_rmab


LIBRARIES_ENDPOINT = "/api/libraries"


class ApiError(RuntimeError):
    def __init__(self, method, path, status):
        super().__init__(f"{method} {path} returned HTTP {status}")
        self.status = status


class Client:
    def __init__(self, base, headers=None):
        self.base = base.rstrip("/")
        self.headers = headers or {}

    def call(self, path, body=None, method=None):
        method = method or ("POST" if body is not None else "GET")
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json", **self.headers},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = response.read()
                return json.loads(data) if data.startswith((b"{", b"[")) else {}
        except urllib.error.HTTPError as error:
            # Upstream error bodies may echo secrets. Never log them.
            raise ApiError(method, path, error.code) from None

    def ready(self, path):
        deadline = time.monotonic() + 180
        while True:
            try:
                return self.call(path)
            except (urllib.error.URLError, TimeoutError, ApiError):
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Service readiness timed out: {path}") from None
                time.sleep(3)

    def authorize(self, token):
        self.headers["Authorization"] = f"Bearer {token}"


def has_audiobooks(categories):
    return any(
        category.get("id") == 3030 or has_audiobooks(category.get("subCategories", []))
        for category in categories
    )


def select_indexers(indexers):
    selected = []
    for indexer in indexers:
        categories = indexer.get("capabilities", {}).get("categories", [])
        if not indexer.get("enable") or indexer.get("protocol") != "torrent":
            continue
        if not has_audiobooks(categories):
            continue
        selected.append(
            {
                "id": indexer["id"],
                "name": indexer["name"],
                "protocol": "torrent",
                "enabled": True,
                "priority": indexer.get("priority", 25),
                "rssEnabled": False,
                "audiobookCategories": [3030],
                "ebookCategories": [],
                "seedingTimeMinutes": 0,
                "ratioLimit": 0,
            }
        )
    if not selected:
        raise RuntimeError(
            "No enabled torrent indexers advertise audiobook category 3030"
        )
    return selected


def provision_abs(client, credentials, token_file):
    if not client.ready("/status")["isInit"]:
        client.call("/init", {"newRoot": credentials})
    login = client.call("/login", credentials)["user"]
    client.authorize(login.get("accessToken") or login["token"])
    libraries = client.call(LIBRARIES_ENDPOINT)["libraries"]
    matches = [
        library
        for library in libraries
        if any(
            folder.get("fullPath", folder.get("path")) == AUDIOBOOK_DIRECTORY
            for folder in library["folders"]
        )
    ]
    if len(matches) > 1:
        raise RuntimeError("Multiple libraries own /data/audiobooks")
    library = (
        matches[0]
        if matches
        else client.call(
            LIBRARIES_ENDPOINT,
            {
                "name": "Audiobooks",
                "folders": [{"fullPath": AUDIOBOOK_DIRECTORY}],
                "mediaType": "book",
                "icon": "audiobooks",
            },
        )
    )
    token = token_file.read_text().strip() if token_file.exists() else None
    if token:
        check = Client(client.base, {"Authorization": f"Bearer {token}"})
        try:
            check.call(LIBRARIES_ENDPOINT)
        except ApiError as error:
            if error.status not in (401, 403):
                raise
            token = None
    if not token:
        key = client.call(
            "/api/api-keys",
            {
                "name": "ReadMeABook (Nix managed)",
                "userId": login["id"],
                "isActive": True,
            },
        )
        token = key["apiKey"]["apiKey"]
        temporary = token_file.with_suffix(".tmp")
        with open(
            temporary, "w", opener=lambda path, flags: os.open(path, flags, 0o600)
        ) as stream:
            stream.write(token)
        temporary.replace(token_file)
    return library["id"], token


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
    readmeabook_credentials = {
        **credentials,
        "password": Path(os.environ["READMEABOOK_PASSWORD_FILE"]).read_text().strip(),
    }
    if not readmeabook_credentials["password"]:
        raise RuntimeError("ReadMeABook password secret is empty")
    provision_rmab(
        Client(os.environ["READMEABOOK_BASE_URL"]),
        readmeabook_credentials,
        library_id,
        token,
        key,
        indexers,
        os.environ["QBITTORRENT_USERNAME"],
        credentials["password"],
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
