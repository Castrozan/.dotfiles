import json
import time
import urllib.error
import urllib.request

MIWAYOMI_REQUEST_TIMEOUT_SECONDS = 10
MIWAYOMI_READINESS_REQUEST_TIMEOUT_SECONDS = 1
MIWAYOMI_READINESS_ATTEMPTS = 40
MIWAYOMI_READINESS_DELAY_SECONDS = 1


def execute(base_url, path, method="GET", payload=None, timeout_seconds=None):
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(
        request, timeout=timeout_seconds or MIWAYOMI_REQUEST_TIMEOUT_SECONDS
    ) as response:
        return json.loads(response.read().decode())


def wait_until_ready(base_url):
    for remaining_attempt in range(MIWAYOMI_READINESS_ATTEMPTS, 0, -1):
        try:
            execute(
                base_url,
                "/api/v1/health",
                timeout_seconds=MIWAYOMI_READINESS_REQUEST_TIMEOUT_SECONDS,
            )
            return True
        except (urllib.error.URLError, OSError, ValueError):
            if remaining_attempt == 1:
                return False
            time.sleep(MIWAYOMI_READINESS_DELAY_SECONDS)
    return False


def read_extension_repository_urls(base_url):
    return execute(base_url, "/api/v1/extensions/repos")["repos"]


def write_extension_repository_urls(base_url, repository_urls):
    execute(
        base_url,
        "/api/v1/extensions/repos",
        method="POST",
        payload={"repos": list(repository_urls)},
    )
    return read_extension_repository_urls(base_url)


def count_extensions_offered(_base_url):
    return None
