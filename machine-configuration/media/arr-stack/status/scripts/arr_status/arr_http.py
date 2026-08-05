import json
import urllib.request

HTTP_REQUEST_TIMEOUT_SECONDS = 15


def get_json(base_url, api_key, path):
    request = urllib.request.Request(
        f"{base_url}{path}",
        method="GET",
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(
        request, timeout=HTTP_REQUEST_TIMEOUT_SECONDS
    ) as response:
        response_body = response.read().decode()
    return json.loads(response_body) if response_body else None
