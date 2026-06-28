import json
import urllib.error
import urllib.parse
import urllib.request


class RemoteMemoryServiceUnavailable(Exception):
    pass


class RemoteRestMemoryBackend:
    backend_name = "remote"

    def __init__(self, base_url, request_timeout_seconds=8.0):
        self.base_url = base_url.rstrip("/")
        self.request_timeout_seconds = request_timeout_seconds

    def is_healthy(self, health_timeout_seconds=3.0):
        for health_path in ("/health", "/healthz", "/docs", "/"):
            try:
                status_code, _ = self._request(
                    "GET", health_path, timeout_seconds=health_timeout_seconds
                )
            except RemoteMemoryServiceUnavailable:
                continue
            if 200 <= status_code < 300:
                return True
        return False

    def add(self, text, user_id):
        _, body = self._request(
            "POST",
            "/memories",
            payload={
                "messages": [{"role": "user", "content": text}],
                "user_id": user_id,
            },
        )
        return body

    def search(self, query, user_id, limit):
        _, body = self._request(
            "POST",
            "/search",
            payload={"query": query, "user_id": user_id, "limit": limit},
        )
        return self._extract_results(body)

    def list_memories(self, user_id):
        _, body = self._request(
            "GET", "/memories?" + urllib.parse.urlencode({"user_id": user_id})
        )
        return self._extract_results(body)

    def delete(self, memory_id):
        _, body = self._request("DELETE", f"/memories/{urllib.parse.quote(memory_id)}")
        return body

    def _extract_results(self, body):
        if isinstance(body, dict) and "results" in body:
            return body["results"]
        return body

    def _request(self, method, path, payload=None, timeout_seconds=None):
        url = self.base_url + path
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        effective_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self.request_timeout_seconds
        )
        try:
            with urllib.request.urlopen(request, timeout=effective_timeout) as response:
                raw = response.read().decode("utf-8") if response.length != 0 else ""
                return response.status, self._parse_json(raw)
        except urllib.error.HTTPError as http_error:
            raise RemoteMemoryServiceUnavailable(
                f"remote returned HTTP {http_error.code} for {method} {path}"
            ) from http_error
        except (urllib.error.URLError, TimeoutError, OSError) as transport_error:
            raise RemoteMemoryServiceUnavailable(
                f"remote unreachable for {method} {path}: {transport_error}"
            ) from transport_error

    def _parse_json(self, raw):
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
