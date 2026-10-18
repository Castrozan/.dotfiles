from urllib.parse import quote, urlsplit

from agent_api.contract import CapabilityError
from agent_api.files import write_json
from agent_api.providers.credentials import read_credential
from agent_api.providers.network import NetworkClient


def fal_queue_url(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "queue.fal.run"
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.fragment
        or parsed.query
        or not parsed.path.startswith("/")
    ):
        raise CapabilityError("invalid_provider_url")
    return url


class CloudProvider:
    def preflight(self, request):
        provider = request.capability.split(".")[0]
        if provider == "monid":
            read_credential("MONID_API_KEY", "monid-api-key")
        elif provider == "fal":
            read_credential("FAL_KEY", "fal-api-key")
            if request.capability == "fal.run":
                endpoint = request.input["endpoint"]
                if any(part in ("", ".", "..") for part in endpoint.split("/")):
                    raise CapabilityError("invalid_endpoint")
            else:
                fal_queue_url(request.input["status_url"])
                fal_queue_url(request.input["response_url"])

    def execute(self, request, directory, operation_id):
        client = NetworkClient(request.timeout_seconds)
        try:
            if request.capability.startswith("monid."):
                return self.monid(request, directory, client)
            if request.capability.startswith("fal."):
                return self.fal(request, directory, client)
            return self.firecrawl(request, client)
        finally:
            client.close()

    def monid(self, request, directory, client):
        credential = read_credential("MONID_API_KEY", "monid-api-key")
        headers = {"Authorization": "Bearer " + credential}
        action = request.capability.split(".")[1]
        base_url = "https://api.monid.ai/v1/"
        if action == "result":
            result = client.json(
                "GET",
                base_url + "runs/" + quote(request.input["run_id"], safe=""),
                headers=headers,
            )
        else:
            result = client.json("POST", base_url + action, request.input, headers)
        if action in ("discover", "inspect"):
            return result
        run_id = result.get("runId")
        if not isinstance(run_id, str) or not run_id or len(run_id) > 256:
            raise CapabilityError("invalid_provider_response")
        write_json(
            directory / "submission.json", {"provider": "monid", "run_id": run_id}
        )
        while result.get("status") not in ("COMPLETED", "FAILED"):
            if action == "result":
                return result
            if result.get("status") not in ("RUNNING", "PENDING", "QUEUED"):
                raise CapabilityError("invalid_provider_response")
            client.pause()
            result = client.json(
                "GET", base_url + "runs/" + quote(run_id, safe=""), headers=headers
            )
        response_status = result.get("providerResponse", {}).get("httpStatus")
        if (
            result["status"] == "FAILED"
            or type(response_status) is not int
            or not 200 <= response_status < 300
        ):
            raise CapabilityError("provider_failed")
        return result

    def fal(self, request, directory, client):
        credential = read_credential("FAL_KEY", "fal-api-key")
        headers = {"Authorization": "Key " + credential}
        if request.capability == "fal.run":
            submission = client.json(
                "POST",
                "https://queue.fal.run/" + request.input["endpoint"],
                request.input["input"],
                headers,
            )
            if not isinstance(submission.get("request_id"), str):
                raise CapabilityError("invalid_provider_response")
            write_json(directory / "submission.json", {"provider": "fal", **submission})
        else:
            submission = request.input
        try:
            status_url = fal_queue_url(submission["status_url"])
            response_url = fal_queue_url(submission["response_url"])
        except (KeyError, TypeError, ValueError):
            raise CapabilityError("invalid_provider_response") from None
        while True:
            status = client.json("GET", status_url, headers=headers)
            if status.get("status") == "COMPLETED":
                if status.get("error"):
                    raise CapabilityError("provider_failed")
                return client.json("GET", response_url, headers=headers)
            if status.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
                raise CapabilityError("invalid_provider_response")
            if request.capability == "fal.result":
                return status
            client.pause()

    def firecrawl(self, request, client):
        credential = read_credential(
            "FIRECRAWL_API_KEY", "firecrawl-api-key", required=False
        )
        headers = {"Authorization": "Bearer " + credential} if credential else {}
        action = "search" if request.capability == "web.search" else "scrape"
        data = dict(request.input)
        if action == "scrape":
            data.update(formats=["markdown"], onlyMainContent=True)
        result = client.json(
            "POST", "https://api.firecrawl.dev/v2/" + action, data, headers
        )
        if result.get("success") is not True:
            raise CapabilityError("provider_failed")
        return result
