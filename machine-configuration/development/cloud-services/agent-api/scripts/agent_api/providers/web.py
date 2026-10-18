import os

import httpx

from agent_api.contract import (
    MAXIMUM_ARTIFACT_BYTES,
    MAXIMUM_RESULT_BYTES,
    CapabilityError,
    validate_url,
)
from agent_api.providers.network import NetworkClient


class WebProvider:
    def preflight(self, request):
        validate_url(request.input["url"])

    def execute(self, request, directory, operation_id):
        client = NetworkClient(request.timeout_seconds)
        maximum = (
            MAXIMUM_ARTIFACT_BYTES
            if request.capability == "web.download"
            else MAXIMUM_RESULT_BYTES
        )
        try:
            return self.fetch(request, directory, client, maximum)
        except (httpx.HTTPError, OSError):
            raise CapabilityError("network_failed") from None
        finally:
            client.close()

    def fetch(self, request, directory, client, maximum):
        url = request.input["url"]
        for _ in range(6):
            validate_url(url)
            with client.client.stream(
                "GET", url, timeout=client.remaining()
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise CapabilityError("invalid_redirect")
                    url = str(response.url.join(location))
                    continue
                if response.status_code != 200:
                    raise CapabilityError("fetch_failed")
                path = directory / "download.bin"
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                size = 0
                with os.fdopen(descriptor, "wb") as output:
                    for chunk in response.iter_bytes():
                        client.remaining()
                        size += len(chunk)
                        if size > maximum:
                            raise CapabilityError("response_too_large")
                        output.write(chunk)
                if request.capability == "web.download":
                    return {
                        "url": url,
                        "artifact": path.name,
                        "content_type": response.headers.get("content-type"),
                        "size_bytes": size,
                    }
                content_type = response.headers.get("content-type", "").split(";")[0]
                if content_type not in (
                    "text/html",
                    "application/xhtml+xml",
                    "text/plain",
                ):
                    raise CapabilityError("unsupported_content_type")
                return self.extract(path, url, content_type)
        raise CapabilityError("too_many_redirects")

    def extract(self, path, url, content_type):
        if content_type == "text/plain":
            markdown = path.read_text(encoding="utf-8", errors="replace")
        else:
            from trafilatura import extract

            markdown = extract(
                path.read_bytes(),
                url=url,
                output_format="markdown",
                include_links=True,
                include_tables=True,
                include_comments=False,
            )
        if not markdown:
            raise CapabilityError("no_content")
        return {"url": url, "markdown": markdown, "javascript_rendered": False}
