import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable


INFO_HASH = re.compile(r"^[0-9a-fA-F]{40}$")
TRACKER_SCHEMES = ("http://", "https://", "udp://")


@dataclass(frozen=True)
class CometResponse:
    status: int
    content_type: str
    cache_control: str | None
    location: str | None
    body: bytes


def normalize_stream(stream: dict) -> dict:
    normalized_sources = []
    seen_sources = set()
    for source in stream.get("sources", []):
        if not isinstance(source, str):
            continue
        if source.startswith(("tracker:", "dht:")):
            normalized_source = source
        elif source.startswith(TRACKER_SCHEMES):
            normalized_source = f"tracker:{source}"
        else:
            continue
        if normalized_source not in seen_sources:
            normalized_sources.append(normalized_source)
            seen_sources.add(normalized_source)

    info_hash = stream.get("infoHash", "")
    if isinstance(info_hash, str) and INFO_HASH.fullmatch(info_hash):
        dht_source = f"dht:{info_hash.lower()}"
        if dht_source not in seen_sources:
            normalized_sources.append(dht_source)

    normalized_stream = dict(stream)
    normalized_stream["sources"] = normalized_sources
    return normalized_stream


def normalize_stream_response(body: bytes) -> bytes:
    payload = json.loads(body)
    payload["streams"] = [normalize_stream(stream) for stream in payload["streams"]]
    return json.dumps(payload, separators=(",", ":")).encode()


def fetch_comet_response(url: str) -> CometResponse:
    try:
        response = urllib.request.urlopen(url, timeout=60)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return CometResponse(
            response.status,
            response.headers.get("Content-Type", "application/octet-stream"),
            response.headers.get("Cache-Control"),
            response.headers.get("Location"),
            response.read(),
        )


class CometStreamAdapter:
    def __init__(
        self,
        comet_url: str,
        request: Callable[[str], CometResponse] = fetch_comet_response,
    ):
        self.comet_url = comet_url.rstrip("/")
        self.request = request

    def response(self, request_target: str) -> CometResponse:
        normalized_target = f"/{request_target.lstrip('/')}"
        response = self.request(f"{self.comet_url}{normalized_target}")
        if "/stream/" not in normalized_target or response.status != 200:
            return response
        return CometResponse(
            response.status,
            response.content_type,
            response.cache_control,
            response.location,
            normalize_stream_response(response.body),
        )
