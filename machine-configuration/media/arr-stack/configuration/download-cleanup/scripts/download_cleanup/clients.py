import json
from urllib.parse import urlencode

from .transport import HttpFailure, HttpTransport


class MediaClient:
    def __init__(self, base_url, api_key, app):
        self.transport = HttpTransport(base_url, {"X-Api-Key": api_key})
        self.app = app
        self.resource = "movie" if app == "radarr" else "series"

    def get(self, path):
        return json.loads(self.transport.request(path))

    def exists(self, identifier):
        try:
            self.get(f"/{self.resource}/{identifier}")
            return True
        except HttpFailure as error:
            if error.status == 404:
                return False
            raise

    def media(self):
        return self.get(f"/{self.resource}")

    def history(self):
        for page in range(1, 21):
            result = self.get(
                f"/history?page={page}&pageSize=1000&sortKey=date&sortDirection=descending"
            )
            yield from result["records"]
            if page * 1000 >= result["totalRecords"]:
                return
        raise RuntimeError("history exceeds bootstrap bound")


class TorrentClient:
    def __init__(self, base_url, username, password):
        self.username = username
        self.password = password
        self.transport = HttpTransport(
            base_url,
            {
                "Referer": base_url + "/",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        self.authenticated = False

    def login(self):
        body = self.transport.request(
            "/api/v2/auth/login",
            "POST",
            urlencode({"username": self.username, "password": self.password}).encode(),
        )
        if body != b"Ok.":
            raise RuntimeError("qBittorrent rejected cleanup login")
        self.authenticated = True

    def request(self, path, fields=None):
        if not self.authenticated:
            self.login()
        arguments = (
            ("GET", None) if fields is None else ("POST", urlencode(fields).encode())
        )
        try:
            return self.transport.request("/api/v2" + path, *arguments)
        except HttpFailure as error:
            if error.status != 403:
                raise
            self.login()
            return self.transport.request("/api/v2" + path, *arguments)

    def list(self):
        return json.loads(self.request("/torrents/info"))

    def delete(self, hashes):
        self.request(
            "/torrents/delete", {"hashes": "|".join(hashes), "deleteFiles": "true"}
        )


class JellyfinClient:
    def __init__(self, base_url, api_key, artifacts):
        self.transport = HttpTransport(base_url, {"X-Emby-Token": api_key})
        self.artifacts = artifacts

    def cleanup(self, media):
        tasks = json.loads(self.transport.request("/ScheduledTasks"))
        task = next(value for value in tasks if value["Key"] == "RefreshLibrary")
        if task["State"] != "Idle":
            raise RuntimeError("Jellyfin library scan is still running")
        if self.artifacts.contains(media):
            self.refresh()
            raise RuntimeError("Jellyfin catalogue removal is pending")
        self.artifacts.clean()

    def refresh(self):
        self.transport.request("/Library/Refresh", "POST")
