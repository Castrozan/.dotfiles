from urllib.parse import quote

from agent_api.contract import CapabilityError
from agent_api.files import write_json
from agent_api.providers.credentials import read_credential
from agent_api.providers.network import NetworkClient

MONID_BASE_URL = "https://api.monid.ai/v1/"


def monid_run_identifier(result):
    run_id = result.get("runId")
    if not isinstance(run_id, str):
        raise CapabilityError("invalid_provider_response")
    if not 1 <= len(run_id) <= 256:
        raise CapabilityError("invalid_provider_response")
    return run_id


def completed_monid_result(result):
    if result.get("status") not in ("COMPLETED", "FAILED"):
        return result
    response_status = result.get("providerResponse", {}).get("httpStatus")
    if type(response_status) is not int:
        raise CapabilityError("provider_failed")
    if result["status"] == "FAILED" or not 200 <= response_status < 300:
        raise CapabilityError("provider_failed")
    return result


class MonidProvider:
    def preflight(self, request):
        read_credential("MONID_API_KEY", "monid-api-key")

    def execute(self, request, directory, operation_id):
        with NetworkClient(request.timeout_seconds) as client:
            return self.run(request, directory, client)

    def run(self, request, directory, client):
        headers = {
            "Authorization": "Bearer "
            + read_credential("MONID_API_KEY", "monid-api-key")
        }
        action = request.capability.split(".")[1]
        result = self.dispatch(request, client, headers)
        if action in ("discover", "inspect"):
            return result
        run_id = monid_run_identifier(result)
        write_json(
            directory / "submission.json", {"provider": "monid", "run_id": run_id}
        )
        if action == "run":
            result = self.await_result(result, client, headers)
        return completed_monid_result(result)

    def dispatch(self, request, client, headers):
        action = request.capability.split(".")[1]
        if action == "result":
            return client.json(
                "GET",
                MONID_BASE_URL + "runs/" + quote(request.input["run_id"], safe=""),
                headers=headers,
            )
        return client.json("POST", MONID_BASE_URL + action, request.input, headers)

    def await_result(self, result, client, headers):
        run_id = monid_run_identifier(result)
        while result.get("status") not in ("COMPLETED", "FAILED"):
            if result.get("status") not in ("RUNNING", "PENDING", "QUEUED"):
                raise CapabilityError("invalid_provider_response")
            client.pause()
            result = client.json(
                "GET",
                MONID_BASE_URL + "runs/" + quote(run_id, safe=""),
                headers=headers,
            )
        return result
