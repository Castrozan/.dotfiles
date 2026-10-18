from agent_api.contract import CapabilityError
from agent_api.providers.credentials import read_credential
from agent_api.providers.network import NetworkClient


class FirecrawlProvider:
    def preflight(self, request):
        pass

    def execute(self, request, directory, operation_id):
        credential = read_credential(
            "FIRECRAWL_API_KEY", "firecrawl-api-key", required=False
        )
        headers = {"Authorization": "Bearer " + credential} if credential else {}
        action = "search" if request.capability == "web.search" else "scrape"
        data = dict(request.input)
        if action == "scrape":
            data.update(formats=["markdown"], onlyMainContent=True)
        with NetworkClient(request.timeout_seconds) as client:
            result = client.json(
                "POST", "https://api.firecrawl.dev/v2/" + action, data, headers
            )
        if result.get("success") is not True:
            raise CapabilityError("provider_failed")
        return result
