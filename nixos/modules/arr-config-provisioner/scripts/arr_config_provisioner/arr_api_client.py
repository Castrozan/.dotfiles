import json
import time
import urllib.request


def request_json(method, url, api_key, body=None):
    encoded_body = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        url,
        data=encoded_body,
        method=method,
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode()
    return json.loads(raw) if raw else None


def wait_for_api_ready(base_url, api_key, attempts=8, delay_seconds=2):
    for attempt in range(attempts):
        try:
            request_json("GET", f"{base_url}/system/status", api_key)
            return True
        except Exception:
            if attempt + 1 >= attempts:
                return False
            time.sleep(delay_seconds)
    return False


def _resource_url(base_url, resource_path, force_save):
    url = f"{base_url}/{resource_path}"
    return f"{url}?forceSave=true" if force_save else url


def get_resource_list(base_url, api_key, resource_path):
    return request_json("GET", f"{base_url}/{resource_path}", api_key) or []


def create_resource(base_url, api_key, resource_path, body, force_save=False):
    return request_json(
        "POST", _resource_url(base_url, resource_path, force_save), api_key, body
    )


def update_resource(
    base_url, api_key, resource_path, resource_id, body, force_save=False
):
    return request_json(
        "PUT",
        _resource_url(base_url, f"{resource_path}/{resource_id}", force_save),
        api_key,
        body,
    )


def get_host_config(base_url, api_key):
    return request_json("GET", f"{base_url}/config/host", api_key)


def update_host_config(base_url, api_key, host_config):
    return request_json(
        "PUT",
        f"{base_url}/config/host/{host_config['id']}",
        api_key,
        host_config,
    )
