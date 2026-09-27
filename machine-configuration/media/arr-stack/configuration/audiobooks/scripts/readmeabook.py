"""Reconcile ReadMeABook request settings and download integrations."""

AUDIOBOOK_DIRECTORY = "/data/audiobooks"


def provision_rmab(
    client,
    credentials,
    library_id,
    abs_token,
    prowlarr_key,
    indexers,
    download_username,
):
    download = {
        "id": "nix-qbittorrent",
        "name": "qBittorrent (Nix managed)",
        "type": "qbittorrent",
        "enabled": True,
        "url": "http://qbittorrent:8080",
        "username": download_username,
        "password": credentials["password"],
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
                    "media_dir": AUDIOBOOK_DIRECTORY,
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
            "mediaDir": AUDIOBOOK_DIRECTORY,
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
