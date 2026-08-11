import json
import time
import urllib.error
import urllib.request


class SeanimeHttpClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def request_json(self, method, path, payload=None, timeout_seconds=5):
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Origin": self.base_url}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.load(response)

    def wait_until_ready(self, attempts=20):
        for _ in range(attempts):
            try:
                self.request_json("GET", "/api/v1/status", timeout_seconds=1)
                return
            except (OSError, urllib.error.URLError, json.JSONDecodeError):
                time.sleep(1)
        raise RuntimeError("Seanime never became reachable")
