"""Minimal HTTP JSON client shared by the audiobook provisioning steps."""

import json
import time
import urllib.error
import urllib.request


class ApiError(RuntimeError):
    def __init__(self, method, path, status):
        super().__init__(f"{method} {path} returned HTTP {status}")
        self.status = status


class Client:
    def __init__(self, base, headers=None):
        self.base = base.rstrip("/")
        self.headers = headers or {}

    def call(self, path, body=None, method=None):
        method = method or ("POST" if body is not None else "GET")
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json", **self.headers},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = response.read()
                return json.loads(data) if data.startswith((b"{", b"[")) else {}
        except urllib.error.HTTPError as error:
            # Upstream error bodies may echo secrets. Never log them.
            raise ApiError(method, path, error.code) from None

    def ready(self, path):
        deadline = time.monotonic() + 180
        while True:
            try:
                return self.call(path)
            except (urllib.error.URLError, TimeoutError, ApiError):
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Service readiness timed out: {path}") from None
                time.sleep(3)

    def authorize(self, token):
        self.headers["Authorization"] = f"Bearer {token}"
