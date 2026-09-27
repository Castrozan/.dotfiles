"""Reconcile audiobook services using APIs; secrets are read only at runtime."""

import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


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


def select_indexers(indexers):
    selected = []
    for indexer in indexers:
        categories = indexer.get("capabilities", {}).get("categories", [])
        if not indexer.get("enable") or indexer.get("protocol") != "torrent":
            continue
        if not any(category.get("id") == 3030 for category in categories):
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
    libraries = client.call("/api/libraries")["libraries"]
    matches = [
        library
        for library in libraries
        if any(
            folder.get("fullPath", folder.get("path")) == "/data/audiobooks"
            for folder in library["folders"]
        )
    ]
    if len(matches) > 1:
        raise RuntimeError("Multiple libraries own /data/audiobooks")
    library = (
        matches[0]
        if matches
        else client.call(
            "/api/libraries",
            {
                "name": "Audiobooks",
                "folders": [{"fullPath": "/data/audiobooks"}],
                "mediaType": "book",
                "icon": "audiobooks",
            },
        )
    )
    token = token_file.read_text().strip() if token_file.exists() else None
    if token:
        check = Client(client.base, {"Authorization": f"Bearer {token}"})
        try:
            check.call("/api/libraries")
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


def provision_rmab(client, credentials, library_id, abs_token, prowlarr_key, indexers):
    download = {
        "id": "nix-qbittorrent",
        "name": "qBittorrent (Nix managed)",
        "type": "qbittorrent",
        "enabled": True,
        "url": "http://qbittorrent:8080",
        **credentials,
        "category": "readmeabook",
        "customPath": "/data/torrents/audiobooks",
        "remotePathMappingEnabled": False,
        "disableSSLVerify": False,
    }
    if not client.ready("/api/setup/status")["setupComplete"]:
        client.call(
            "/api/setup/complete",
            {
                "backendMode": "audiobookshelf",
                "audibleRegion": "us",
                "admin": credentials,
                "authMethod": "manual",
                "registration": {"require_admin_approval": True},
                "audiobookshelf": {
                    "server_url": "http://audiobookshelf:80",
                    "api_token": abs_token,
                    "library_id": library_id,
                    "trigger_scan_after_import": True,
                },
                "prowlarr": {
                    "url": "http://prowlarr:9696",
                    "api_key": prowlarr_key,
                    "indexers": indexers,
                },
                "downloadClient": [download],
                "paths": {
                    "download_dir": "/data/torrents",
                    "media_dir": "/data/audiobooks",
                    "metadata_tagging_enabled": False,
                },
            },
        )
    login = client.call("/api/auth/local/login", credentials)
    client.authorize(login["accessToken"])
    settings = {
        "audiobookshelf": {
            "serverUrl": "http://audiobookshelf:80",
            "apiToken": abs_token,
            "libraryId": library_id,
            "triggerScanAfterImport": True,
        },
        "prowlarr": {"url": "http://prowlarr:9696", "apiKey": prowlarr_key},
        "prowlarr/indexers": {"indexers": indexers},
        "registration": {"enabled": False, "requireAdminApproval": True},
        "ebook": {
            "annasArchiveEnabled": False,
            "indexerSearchEnabled": False,
            "autoGrabEnabled": False,
            "kindleFixEnabled": False,
        },
        "paths": {
            "downloadDir": "/data/torrents",
            "mediaDir": "/data/audiobooks",
            "metadataTaggingEnabled": False,
            "chapterMergingEnabled": False,
            "plexFormatCoercionEnabled": False,
            "fileChmod": "664",
            "dirChmod": "775",
        },
    }
    for name, body in settings.items():
        client.call(f"/api/admin/settings/{name}", body, "PUT")
    clients = client.call("/api/admin/settings/download-clients")["clients"]
    managed = next((item for item in clients if item["name"] == download["name"]), None)
    if managed:
        client.call(
            f"/api/admin/settings/download-clients/{managed['id']}", download, "PUT"
        )
    else:
        client.call("/api/admin/settings/download-clients", download)
    ai = client.call("/api/bookdate/config").get("config")
    if ai and ai.get("isEnabled"):
        client.call(
            "/api/bookdate/config",
            {
                "provider": ai["provider"],
                "model": ai["model"],
                "baseUrl": ai.get("baseUrl"),
                "isEnabled": False,
            },
        )
    print(
        "Audiobook accounts, library and download integrations reconciled; ebook/AI features disabled."
    )


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
