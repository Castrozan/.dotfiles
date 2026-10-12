import functools
import json
import threading
import time
import urllib.parse
import urllib.request


TORBOX_API_URL = "https://api.torbox.app/v1/api/torrents"
DOWNLOAD_LINK_CACHE_SECONDS = 300
MAXIMUM_API_RESPONSE_BYTES = 2 * 1024 * 1024


def request_torbox_json(request: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read(MAXIMUM_API_RESPONSE_BYTES + 1)
        if len(body) > MAXIMUM_API_RESPONSE_BYTES:
            raise RuntimeError("TorBox response exceeds the size limit")
        payload = json.loads(body)
        if not payload.get("success"):
            raise RuntimeError("TorBox API request was rejected")
        return payload
    except Exception:
        raise RuntimeError("TorBox API request failed") from None


class TorBoxDownloadResolver:
    def __init__(self, api_key: str, request=request_torbox_json):
        self.api_key = api_key
        self.request = request
        self.download_lock = threading.Lock()

    def download_url(self, request_target: str) -> str:
        target = urllib.parse.urlsplit(request_target)
        info_hash = target.path.split("/playback/", 1)[1].split("/", 1)[0]
        filename = urllib.parse.parse_qs(target.query).get("torrent_name", [""])[0]
        if not filename:
            raise RuntimeError("TorBox playback filename is missing")
        cache_period = int(time.monotonic() / DOWNLOAD_LINK_CACHE_SECONDS)
        with self.download_lock:
            return self._download_url(info_hash, filename, cache_period)

    @functools.lru_cache(maxsize=128)
    def _download_url(self, info_hash: str, filename: str, cache_period: int) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "User-Agent": "Comet"}
        payload = self.request(
            urllib.request.Request(
                f"{TORBOX_API_URL}/mylist?bypass_cache=true", headers=headers
            )
        )
        torrent = next(
            (
                torrent
                for torrent in payload["data"]
                if torrent.get("hash") == info_hash
            ),
            None,
        )
        if torrent is None:
            raise RuntimeError("TorBox cached torrent is unavailable")
        files = [
            file
            for file in torrent.get("files", [])
            if file.get("name", "").rsplit("/", 1)[-1] == filename
        ]
        if len(files) != 1:
            raise RuntimeError("TorBox cached episode file is unavailable or ambiguous")
        query = urllib.parse.urlencode(
            {
                "token": self.api_key,
                "torrent_id": torrent["id"],
                "file_id": files[0]["id"],
            }
        )
        payload = self.request(
            urllib.request.Request(
                f"{TORBOX_API_URL}/requestdl?{query}", headers=headers
            )
        )
        download_url = payload.get("data")
        if not isinstance(download_url, str) or not download_url.startswith("https://"):
            raise RuntimeError("TorBox download URL is invalid")
        return download_url
