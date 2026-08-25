import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree
from dataclasses import dataclass
from pathlib import Path


VALID_INFO_HASH = re.compile(r"^[a-fA-F0-9]{40}$")
STREAM_PATH = re.compile(
    r"^/prowlarr/stream/(?P<media_type>movie|series)/(?P<identifier>tt\d+(?::\d+:\d+)?)\.json$"
)
MOVIE_COLLECTION_WORDS = re.compile(
    r"\b(collection|complete|duology|trilogy|quadrilogy|saga|pack)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class StreamRequest:
    media_type: str
    imdb_identifier: str
    season: int | None = None
    episode: int | None = None


def read_prowlarr_api_key(config_file: Path) -> str:
    root = xml.etree.ElementTree.parse(config_file).getroot()
    api_key = root.findtext("ApiKey", "").strip()
    if not api_key:
        raise RuntimeError("Prowlarr API key is missing")
    return api_key


def parse_stream_request(path: str) -> StreamRequest | None:
    match = STREAM_PATH.fullmatch(path)
    if match is None:
        return None
    identifier_parts = match.group("identifier").split(":")
    if match.group("media_type") == "movie" and len(identifier_parts) == 1:
        return StreamRequest("movie", identifier_parts[0])
    if match.group("media_type") == "series" and len(identifier_parts) == 3:
        return StreamRequest(
            "series",
            identifier_parts[0],
            int(identifier_parts[1]),
            int(identifier_parts[2]),
        )
    return None


def addon_manifest() -> dict:
    return {
        "id": "com.lucaszanoni.prowlarr-streams",
        "version": "1.0.0",
        "name": "Prowlarr Streams",
        "description": "Instant private movie and TV streams from Prowlarr",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"],
        "catalogs": [],
        "behaviorHints": {"p2p": True, "configurable": False},
    }


def setup_url(web_url: str, streaming_server_url: str, addon_manifest_url: str) -> str:
    route_query = urllib.parse.urlencode(
        {
            "addon": addon_manifest_url,
            "streamingServerUrl": streaming_server_url,
        }
    )
    return f"{web_url.rstrip('/')}/#/addons?{route_query}"


def request_json(url: str, headers: dict[str, str] | None = None) -> object:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def category_identifiers(result: dict) -> set[int]:
    return {
        category["id"]
        for category in result.get("categories", [])
        if isinstance(category, dict) and isinstance(category.get("id"), int)
    }


def result_matches_media_type(result: dict, media_type: str) -> bool:
    identifiers = category_identifiers(result)
    category_range = range(2000, 3000) if media_type == "movie" else range(5000, 6000)
    return any(identifier in category_range for identifier in identifiers)


def result_info_hash(result: dict) -> str:
    nested_torrent = result.get("torrent") or {}
    candidate = str(result.get("infoHash") or nested_torrent.get("infoHash") or "")
    return candidate.upper() if VALID_INFO_HASH.fullmatch(candidate) else ""


def release_matches_request(result: dict, stream_request: StreamRequest) -> bool:
    title = str(result.get("title") or "")
    if stream_request.media_type == "movie":
        return MOVIE_COLLECTION_WORDS.search(title) is None
    episode_marker = re.compile(
        rf"\bS0*{stream_request.season}E0*{stream_request.episode}\b",
        re.IGNORECASE,
    )
    return episode_marker.search(title) is not None


def human_size(byte_count: int) -> str:
    value = float(max(byte_count, 0))
    for suffix in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if value < 1024 or suffix == "TiB":
            return f"{value:.1f} {suffix}"
        value /= 1024
    raise AssertionError


def stream_from_result(result: dict) -> dict:
    seeders = max(int(result.get("seeders") or 0), 0)
    size = max(int(result.get("size") or 0), 0)
    return {
        "name": "Prowlarr",
        "title": f"{human_size(size)} | {seeders} seeders\n{result['title']}",
        "infoHash": result_info_hash(result),
        "behaviorHints": {"bingeGroup": f"prowlarr-{result_info_hash(result).lower()}"},
    }


class ProwlarrStreamProvider:
    def __init__(
        self,
        prowlarr_url: str,
        prowlarr_api_key: str,
        metadata_url: str,
        json_request=request_json,
    ):
        self.prowlarr_url = prowlarr_url.rstrip("/")
        self.prowlarr_api_key = prowlarr_api_key
        self.metadata_url = metadata_url.rstrip("/")
        self.json_request = json_request

    def streams(self, stream_request: StreamRequest) -> list[dict]:
        metadata = self._metadata(stream_request)
        query = self._search_query(stream_request, metadata)
        results = self._search(query)
        candidates = [
            result
            for result in results
            if result.get("protocol") == "torrent"
            and result.get("title")
            and result_info_hash(result)
            and result_matches_media_type(result, stream_request.media_type)
            and release_matches_request(result, stream_request)
        ]
        candidates.sort(
            key=lambda result: (
                -max(int(result.get("seeders") or 0), 0),
                max(int(result.get("size") or 0), 0),
            )
        )
        return [stream_from_result(result) for result in candidates[:20]]

    def _metadata(self, stream_request: StreamRequest) -> dict:
        metadata_endpoint = (
            f"{self.metadata_url}/meta/{stream_request.media_type}/"
            f"{stream_request.imdb_identifier}.json"
        )
        response = self.json_request(metadata_endpoint)
        metadata = response.get("meta") if isinstance(response, dict) else None
        if not isinstance(metadata, dict) or not metadata.get("name"):
            raise RuntimeError("Cinemeta returned no title")
        return metadata

    def _search_query(self, stream_request: StreamRequest, metadata: dict) -> str:
        if stream_request.media_type == "series":
            return (
                f"{metadata['name']} S{stream_request.season:02}"
                f"E{stream_request.episode:02} 1080p"
            )
        year = str(metadata.get("year") or metadata.get("releaseInfo") or "")[:4]
        return " ".join(part for part in [metadata["name"], year, "1080p"] if part)

    def _search(self, query: str) -> list[dict]:
        search_url = f"{self.prowlarr_url}/api/v1/search?{urllib.parse.urlencode({'query': query})}"
        response = self.json_request(
            search_url,
            {"X-Api-Key": self.prowlarr_api_key, "Accept": "application/json"},
        )
        return response if isinstance(response, list) else []
