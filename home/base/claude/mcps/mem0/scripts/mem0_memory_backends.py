import json
import os
import urllib.error
import urllib.parse
import urllib.request


class RemoteUnavailable(Exception):
    pass


class RemoteMemory:
    backend_name = "remote"

    def __init__(self, base_url, request_timeout_seconds=8.0):
        self.base_url = base_url.rstrip("/")
        self.request_timeout_seconds = request_timeout_seconds

    def is_healthy(self, health_timeout_seconds=3.0):
        for path in ("/health", "/healthz", "/docs", "/"):
            try:
                status, _ = self._request("GET", path, timeout=health_timeout_seconds)
            except RemoteUnavailable:
                continue
            if 200 <= status < 300:
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
        return self._results(body)

    def list_memories(self, user_id):
        _, body = self._request(
            "GET", "/memories?" + urllib.parse.urlencode({"user_id": user_id})
        )
        return self._results(body)

    def delete(self, memory_id):
        _, body = self._request("DELETE", f"/memories/{urllib.parse.quote(memory_id)}")
        return body

    def _results(self, body):
        return body["results"] if isinstance(body, dict) and "results" in body else body

    def _request(self, method, path, payload=None, timeout=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(
                request, timeout=timeout or self.request_timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
                return response.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as error:
            raise RemoteUnavailable(
                f"remote HTTP {error.code} for {method} {path}"
            ) from error
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise RemoteUnavailable(
                f"remote unreachable for {method} {path}: {error}"
            ) from error


class LocalNoLlmMemory:
    backend_name = "local"

    def __init__(self, store_directory, embedding_model, collection_name):
        self.store_directory = store_directory
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self._memory = None

    def is_healthy(self, health_timeout_seconds=None):
        return True

    def add(self, text, user_id):
        return self._unwrap(self._instance().add(text, user_id=user_id, infer=False))

    def search(self, query, user_id, limit):
        return self._unwrap(
            self._instance().search(query, filters={"user_id": user_id}, limit=limit)
        )

    def list_memories(self, user_id):
        return self._unwrap(self._instance().get_all(filters={"user_id": user_id}))

    def delete(self, memory_id):
        return self._instance().delete(memory_id=memory_id)

    def _unwrap(self, result):
        if isinstance(result, dict) and "results" in result:
            return result["results"]
        return result

    def _instance(self):
        if self._memory is not None:
            return self._memory
        for key, value in {
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
            "CUDA_VISIBLE_DEVICES": "",
            "TOKENIZERS_PARALLELISM": "false",
            "ANONYMIZED_TELEMETRY": "False",
            "HF_HUB_DISABLE_TELEMETRY": "1",
        }.items():
            os.environ.setdefault(key, value)
        os.makedirs(self.store_directory, exist_ok=True)
        from mem0 import Memory

        self._memory = Memory.from_config(
            {
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "path": self.store_directory,
                        "collection_name": self.collection_name,
                    },
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": self.embedding_model,
                        "model_kwargs": {"device": "cpu"},
                    },
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "api_key": "local-no-llm-because-add-uses-infer-false",
                        "model": "gpt-4o-mini",
                    },
                },
            }
        )
        return self._memory
