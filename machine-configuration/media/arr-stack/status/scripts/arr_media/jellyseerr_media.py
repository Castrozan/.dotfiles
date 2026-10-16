import http.client
import json
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import urlencode


@dataclass(frozen=True)
class JellyseerrRequestError(Exception):
    status: int


@dataclass(frozen=True)
class JellyseerrMedia:
    api_key: str
    requester_id: int | None = None

    def request(self, method, path, payload=None):
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
        if self.requester_id is not None:
            headers["X-API-User"] = str(self.requester_id)
        connection = http.client.HTTPConnection("127.0.0.1", 5055, timeout=20)
        try:
            connection.request(
                method,
                f"/api/v1{path}",
                body=json.dumps(payload).encode() if payload is not None else None,
                headers=headers,
            )
            response = connection.getresponse()
            if response.status >= 400:
                raise JellyseerrRequestError(response.status)
            return json.loads(response.read())
        finally:
            connection.close()

    def search(self, title):
        query = urlencode({"query": title, "page": 1, "language": "pt-BR"})
        results = self.request("GET", f"/search?{query}")["results"]
        return [
            catalog_entry(result, result["mediaType"])
            for result in results
            if result.get("mediaType") in {"movie", "tv"}
        ][:20]

    def details(self, media_type, media_id):
        return self.request("GET", f"/{media_type}/{media_id}?language=pt-BR")

    def public_requests(self, details):
        return [
            request
            for request in (details.get("mediaInfo") or {}).get("requests", [])
            if (request.get("requestedBy") or {}).get("id") == self.requester_id
            and not request.get("is4k")
        ]


def public_requester(stack_home):
    settings_file = Path(stack_home) / "config/jellyseerr/settings.json"
    api_key = json.loads(settings_file.read_text())["main"]["apiKey"]
    if not api_key:
        raise ValueError("Jellyseerr credentials are unavailable")
    administrator = JellyseerrMedia(api_key)
    users = administrator.request("GET", "/user?take=200")["results"]
    matches = [user for user in users if user.get("jellyfinUsername") == "lucas"]
    if len(matches) != 1:
        raise ValueError("Public Jellyseerr requester is unavailable")
    requester = matches[0]
    validate_public_requester(requester)
    return replace(administrator, requester_id=requester["id"])


def validate_public_requester(requester):
    if requester["id"] == 1 or int(requester.get("permissions") or 0) & (
        2 | 16 | 16384
    ):
        raise ValueError("Public Jellyseerr requester must have ordinary permissions")


def catalog_entry(details, media_type):
    return {
        "media_type": media_type,
        "media_id": details["id"],
        "title": details.get("title") or details.get("name"),
        "original_title": details.get("originalTitle") or details.get("originalName"),
        "year": (details.get("releaseDate") or details.get("firstAirDate") or "")[:4],
    }


def public_status(client, details, media_type):
    requests = client.public_requests(details)
    result = catalog_entry(details, media_type)
    result["seasons"] = [
        season["seasonNumber"]
        for season in details.get("seasons", [])
        if season["seasonNumber"] > 0 and season.get("episodeCount", 0) > 0
    ]
    result["requests"] = [
        {
            "request_id": request["id"],
            "status": {
                1: "pending",
                2: "approved",
                3: "declined",
                4: "failed",
                5: "completed",
            }.get(request["status"], "unknown"),
            "seasons": [
                season["seasonNumber"] for season in request.get("seasons", [])
            ],
        }
        for request in requests
    ]
    if requests:
        result["availability"] = {
            1: "unknown",
            2: "pending",
            3: "processing",
            4: "partial",
            5: "available",
        }.get((details.get("mediaInfo") or {}).get("status"), "unknown")
    return result
