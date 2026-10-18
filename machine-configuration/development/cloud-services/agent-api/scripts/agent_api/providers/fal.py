from urllib.parse import urlsplit

from agent_api.contract import CapabilityError
from agent_api.files import write_json
from agent_api.providers.credentials import read_credential
from agent_api.providers.network import NetworkClient


def fal_queue_url(url):
    parsed = urlsplit(url)
    valid = (
        parsed.scheme == "https",
        parsed.hostname == "queue.fal.run",
        parsed.port in (None, 443),
        parsed.username is None,
        not parsed.fragment,
        not parsed.query,
        parsed.path.startswith("/"),
    )
    if not all(valid):
        raise CapabilityError("invalid_provider_url")
    return url


def fal_submission_urls(submission):
    try:
        return fal_queue_url(submission["status_url"]), fal_queue_url(
            submission["response_url"]
        )
    except (KeyError, TypeError, ValueError):
        raise CapabilityError("invalid_provider_response") from None


class FalProvider:
    def preflight(self, request):
        read_credential("FAL_KEY", "fal-api-key")
        if request.capability == "fal.result":
            fal_submission_urls(request.input)
            return
        if any(
            part in ("", ".", "..") for part in request.input["endpoint"].split("/")
        ):
            raise CapabilityError("invalid_endpoint")

    def execute(self, request, directory, operation_id):
        with NetworkClient(request.timeout_seconds) as client:
            return self.run(request, directory, client)

    def run(self, request, directory, client):
        headers = {"Authorization": "Key " + read_credential("FAL_KEY", "fal-api-key")}
        submission = self.submit(request, directory, client, headers)
        status_url, response_url = fal_submission_urls(submission)
        while True:
            status = client.json("GET", status_url, headers=headers)
            if status.get("status") == "COMPLETED":
                return self.completed_result(status, response_url, client, headers)
            self.validate_pending(status)
            if request.capability == "fal.result":
                return status
            client.pause()

    def submit(self, request, directory, client, headers):
        if request.capability == "fal.result":
            return request.input
        submission = client.json(
            "POST",
            "https://queue.fal.run/" + request.input["endpoint"],
            request.input["input"],
            headers,
        )
        if not isinstance(submission.get("request_id"), str):
            raise CapabilityError("invalid_provider_response")
        write_json(directory / "submission.json", {"provider": "fal", **submission})
        return submission

    def validate_pending(self, status):
        if status.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
            raise CapabilityError("invalid_provider_response")

    def completed_result(self, status, response_url, client, headers):
        if status.get("error"):
            raise CapabilityError("provider_failed")
        return client.json("GET", response_url, headers=headers)
