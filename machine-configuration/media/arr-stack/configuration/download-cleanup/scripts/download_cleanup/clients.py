import http.cookiejar
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


def response_body(response):
    body = response.read(16 * 1024 * 1024 + 1)
    if len(body) > 16 * 1024 * 1024:
        raise ValueError("application response exceeds size limit")
    return body


class MediaClient:
    def __init__(self, base_url, api_key, app):
        self.base_url = base_url
        self.api_key = api_key
        self.app = app
        self.resource = "movie" if app == "radarr" else "series"

    def get(self, path):
        request = Request(self.base_url + path, headers={"X-Api-Key": self.api_key})
        with build_opener().open(request, timeout=5) as response:
            return json.loads(response_body(response))

    def exists(self, identifier):
        try:
            self.get(f"/{self.resource}/{identifier}")
            return True
        except HTTPError as error:
            if error.code == 404:
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
        self.base_url = base_url
        self.username = username
        self.password = password
        self.opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.authenticated = False

    def login(self):
        request = Request(
            self.base_url + "/api/v2/auth/login",
            data=urlencode(
                {"username": self.username, "password": self.password}
            ).encode(),
            headers={"Referer": self.base_url + "/"},
        )
        with self.opener.open(request, timeout=5) as response:
            if response_body(response) != b"Ok.":
                raise RuntimeError("qBittorrent rejected cleanup login")
        self.authenticated = True

    def request(self, path, fields=None):
        if not self.authenticated:
            self.login()
        request = Request(
            self.base_url + "/api/v2" + path,
            data=urlencode(fields).encode() if fields is not None else None,
            headers={"Referer": self.base_url + "/"},
        )
        try:
            with self.opener.open(request, timeout=5) as response:
                return response_body(response)
        except HTTPError as error:
            if error.code != 403:
                raise
            self.authenticated = False
            self.login()
            with self.opener.open(request, timeout=5) as response:
                return response_body(response)

    def list(self):
        return json.loads(self.request("/torrents/info"))

    def delete(self, hashes):
        self.request(
            "/torrents/delete", {"hashes": "|".join(hashes), "deleteFiles": "true"}
        )


class JellyfinClient:
    def __init__(self, base_url, api_key, artifacts):
        self.base_url = base_url
        self.api_key = api_key
        self.artifacts = artifacts

    def cleanup(self, media):
        request = Request(
            self.base_url + "/ScheduledTasks",
            headers={"X-Emby-Token": self.api_key},
        )
        with build_opener().open(request, timeout=5) as response:
            tasks = json.loads(response_body(response))
        task = next(value for value in tasks if value["Key"] == "RefreshLibrary")
        if task["State"] != "Idle":
            raise RuntimeError("Jellyfin library scan is still running")
        if self.artifacts.contains(media):
            self.refresh()
            raise RuntimeError("Jellyfin catalogue removal is pending")
        self.artifacts.clean()

    def refresh(self):
        request = Request(
            self.base_url + "/Library/Refresh",
            method="POST",
            headers={"X-Emby-Token": self.api_key},
        )
        with build_opener().open(request, timeout=5) as response:
            response_body(response)
