import http.client
import json
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

PUBLIC_LIBRARY_DIRECTORIES = {"movie": "/data/media/movies", "tv": "/data/media/tv"}


@dataclass(frozen=True)
class MediaLibrary:
    address: str
    port: int
    api_key: str
    resource: str

    def item(self, identifier):
        connection = http.client.HTTPConnection(self.address, self.port, timeout=20)
        try:
            connection.request(
                "GET",
                f"/api/v3/{self.resource}/{identifier}",
                headers={"X-Api-Key": self.api_key},
            )
            response = connection.getresponse()
            if response.status == 404:
                return None
            if response.status != 200:
                raise ValueError("Library lookup failed")
            return json.loads(response.read())
        finally:
            connection.close()


def load_media_library(stack_home, media_type, service_identifier):
    stack = Path(stack_home)
    application, port, resource = (
        ("radarr", 7878, "movie")
        if media_type == "movie"
        else ("sonarr", 8989, "series")
    )
    settings = json.loads((stack / "config/jellyseerr/settings.json").read_text())
    services = [
        service
        for service in settings[application]
        if not service.get("is4k")
        and (
            service.get("id") == service_identifier
            if service_identifier is not None and service_identifier >= 0
            else service.get("isDefault")
        )
    ]
    if len(services) != 1 or any(
        (
            services[0].get("hostname") != f"arr-{application}",
            services[0].get("port") != port,
            bool(services[0].get("useSsl")),
            bool(services[0].get("baseUrl")),
            services[0].get("activeDirectory")
            != PUBLIC_LIBRARY_DIRECTORIES[media_type],
        )
    ):
        raise ValueError("Removal service is not the public stack library")
    addresses = [
        line.partition("=")[2].strip()
        for line in (stack / ".env").read_text().splitlines()
        if line.startswith("ARR_BIND_ADDR=")
    ]
    try:
        key = ElementTree.parse(stack / "config" / application / "config.xml").findtext(
            "ApiKey"
        )
    except ElementTree.ParseError as error:
        raise ValueError("Library credentials are unavailable") from error
    if len(addresses) != 1 or not addresses[0] or not key:
        raise ValueError("Library credentials are unavailable")
    return MediaLibrary(addresses[0], port, key, resource)
