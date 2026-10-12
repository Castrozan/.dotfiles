import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, replace
from typing import Callable

from torbox_download_resolver import TorBoxDownloadResolver

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
    if "infoHash" not in stream:
        return stream
    normalized_sources, seen_sources = _normalized_sources(stream.get("sources", []))
    _append_dht_source(normalized_sources, seen_sources, stream.get("infoHash", ""))

    normalized_stream = dict(stream)
    normalized_stream["sources"] = normalized_sources
    return normalized_stream


def _normalized_sources(sources):
    normalized_sources = []
    seen_sources = set()
    for source in sources:
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
    return normalized_sources, seen_sources


def _append_dht_source(normalized_sources, seen_sources, info_hash):
    if isinstance(info_hash, str) and INFO_HASH.fullmatch(info_hash):
        dht_source = f"dht:{info_hash.lower()}"
        if dht_source not in seen_sources:
            normalized_sources.append(dht_source)


def normalize_stream_response(body: bytes) -> bytes:
    payload = json.loads(body)
    payload["streams"] = [normalize_stream(stream) for stream in payload["streams"]]
    return json.dumps(payload, separators=(",", ":")).encode()


class PreservePlaybackRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, status, message, headers, new_url):
        return None


def fetch_comet_response(url: str) -> CometResponse:
    opener = urllib.request.build_opener(PreservePlaybackRedirect())
    try:
        response = opener.open(url, timeout=60)
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
        configuration: dict,
        api_key: str,
        request: Callable[[str], CometResponse] = fetch_comet_response,
    ):
        if not api_key.strip():
            raise ValueError("TorBox API key is missing")
        self.comet_url = comet_url.rstrip("/")
        self.public_configuration = base64.b64encode(
            json.dumps(configuration, separators=(",", ":")).encode()
        ).decode()
        private_configuration = configuration | {
            "debridApiKey": api_key.strip(),
            "debridServices": [],
            "debridStreamProxyPassword": "",
        }
        self.private_configuration = base64.b64encode(
            json.dumps(private_configuration, separators=(",", ":")).encode()
        ).decode()
        self.request = request
        self.download_resolver = TorBoxDownloadResolver(api_key.strip())

    def response(self, request_target: str, request_origin: str) -> CometResponse:
        target = urllib.parse.urlsplit(f"/{request_target.lstrip('/')}")
        path_segments = target.path.lstrip("/").split("/")
        route_offset = (
            0 if path_segments[0] in {"manifest.json", "stream", "playback"} else 1
        )
        route_segments = path_segments[route_offset:]
        if not route_segments or route_segments[0] not in {
            "manifest.json",
            "stream",
            "playback",
        }:
            return CometResponse(404, "application/json", "no-store", None, b"{}")
        encoded_configuration = (
            self.public_configuration
            if route_segments[0] == "manifest.json"
            else self.private_configuration
        )
        upstream_path = "/" + "/".join([encoded_configuration, *route_segments])
        upstream_target = urllib.parse.urlunsplit(
            ("", "", upstream_path, target.query, "")
        )
        try:
            response = self.request(f"{self.comet_url}{upstream_target}")
        except Exception:
            raise RuntimeError("Comet upstream request failed") from None
        if route_segments[0] == "playback" and response.status == 302:
            response = replace(
                response, location=self.download_resolver.download_url(request_target)
            )
        public_body = response.body.replace(
            self.private_configuration.encode(), self.public_configuration.encode()
        )
        public_location = self._public_playback_url(response.location, request_origin)
        if "/stream/" not in upstream_path or response.status != 200:
            if public_body != response.body or public_location != response.location:
                return CometResponse(
                    response.status,
                    response.content_type,
                    response.cache_control,
                    public_location,
                    public_body,
                )
            return response
        payload = json.loads(normalize_stream_response(response.body))
        for stream in payload["streams"]:
            if "url" in stream:
                stream["url"] = self._public_playback_url(stream["url"], request_origin)
        body = (
            json.dumps(payload, separators=(",", ":"))
            .encode()
            .replace(
                self.private_configuration.encode(), self.public_configuration.encode()
            )
        )
        return CometResponse(
            response.status,
            response.content_type,
            response.cache_control,
            public_location,
            body,
        )

    def _public_playback_url(
        self, playback_url: str | None, request_origin: str
    ) -> str | None:
        if not isinstance(playback_url, str):
            return playback_url
        playback = urllib.parse.urlsplit(playback_url)
        private_prefix = f"/{self.private_configuration}/playback/"
        if not playback.path.startswith(private_prefix):
            return playback_url
        public_path = playback.path.replace(
            private_prefix, f"/comet/{self.public_configuration}/playback/", 1
        )
        return request_origin.rstrip("/") + urllib.parse.urlunsplit(
            ("", "", public_path, playback.query, "")
        )
