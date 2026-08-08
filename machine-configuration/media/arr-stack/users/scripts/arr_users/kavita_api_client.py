import json
import time
import urllib.error
import urllib.parse
import urllib.request

KAVITA_REQUEST_TIMEOUT_SECONDS = 20
KAVITA_READINESS_ATTEMPTS = 30
KAVITA_READINESS_DELAY_SECONDS = 4
KAVITA_PLUGIN_NAME = "arr-users-library-access"


def request_json(base_url, bearer_token, method, path, payload=None):
    encoded_payload = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=encoded_payload,
        method=method,
        headers=headers,
    )
    with urllib.request.urlopen(
        request, timeout=KAVITA_REQUEST_TIMEOUT_SECONDS
    ) as response:
        response_body = response.read().decode()
    return json.loads(response_body) if response_body else None


def authenticate(base_url, api_key):
    query_string = urllib.parse.urlencode(
        {"apiKey": api_key, "pluginName": KAVITA_PLUGIN_NAME}
    )
    session = request_json(
        base_url, None, "POST", f"/api/Plugin/authenticate?{query_string}"
    )
    bearer_token = (session or {}).get("token")
    if not bearer_token:
        raise ValueError(
            f"Kavita at {base_url} accepted the admin API key but returned no bearer "
            "token, so no account policy could be written"
        )
    return bearer_token


def wait_for_bearer_token(base_url, api_key):
    for remaining_attempt in range(KAVITA_READINESS_ATTEMPTS, 0, -1):
        try:
            return authenticate(base_url, api_key)
        except urllib.error.HTTPError as error:
            if error.code < 500:
                raise
            if remaining_attempt == 1:
                return None
            time.sleep(KAVITA_READINESS_DELAY_SECONDS)
        except (urllib.error.URLError, OSError):
            if remaining_attempt == 1:
                return None
            time.sleep(KAVITA_READINESS_DELAY_SECONDS)
    return None


def list_users(base_url, bearer_token):
    return request_json(base_url, bearer_token, "GET", "/api/Users") or []


def list_libraries(base_url, bearer_token):
    return request_json(base_url, bearer_token, "GET", "/api/Library/libraries") or []


def update_account(base_url, bearer_token, account_update):
    request_json(base_url, bearer_token, "POST", "/api/Account/update", account_update)


def update_library(base_url, bearer_token, library_update):
    request_json(base_url, bearer_token, "POST", "/api/Library/update", library_update)
