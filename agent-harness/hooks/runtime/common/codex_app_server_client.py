from dataclasses import dataclass
import hashlib
import json
import time


class CodexAppServerError(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexThreadTitle:
    name: str | None
    preview: str

    @property
    def name_digest(self) -> str:
        return hashlib.sha256((self.name or "").encode()).hexdigest()


class CodexAppServerClient:
    def __init__(self, socket_path: str, timeout_seconds: float = 1.0):
        from websockets.sync.client import unix_connect

        self.deadline = time.monotonic() + timeout_seconds
        self.request_number = 0
        self.connection = unix_connect(
            socket_path,
            uri="ws://localhost",
            open_timeout=self.remaining_seconds(),
            close_timeout=0.1,
            max_size=1024 * 1024,
        )
        try:
            self.request(
                "initialize",
                {"clientInfo": {"name": "dotfiles_codex_session", "version": "1"}},
            )
            self.connection.send(json.dumps({"method": "initialized", "params": {}}))
        except Exception:
            self.connection.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.connection.close()

    def remaining_seconds(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Codex session metadata request timed out")
        return remaining

    def request(self, method: str, parameters: dict) -> dict:
        self.request_number += 1
        self.connection.send(
            json.dumps(
                {"id": self.request_number, "method": method, "params": parameters}
            )
        )
        while True:
            response = json.loads(
                self.connection.recv(timeout=self.remaining_seconds())
            )
            if (
                not isinstance(response, dict)
                or response.get("id") != self.request_number
            ):
                continue
            if "error" in response:
                raise CodexAppServerError(
                    f"{method}: {response['error'].get('message', 'request failed')}"
                )
            result = response.get("result")
            if not isinstance(result, dict):
                raise CodexAppServerError(f"{method}: invalid response")
            return result

    def thread_title(self, thread_identifier: str) -> CodexThreadTitle:
        result = self.request(
            "thread/read", {"threadId": thread_identifier, "includeTurns": False}
        )
        name = result["thread"].get("name")
        if name is not None and not isinstance(name, str):
            raise CodexAppServerError("thread/read: invalid thread name")
        preview = result["thread"].get("preview", "")
        if not isinstance(preview, str):
            raise CodexAppServerError("thread/read: invalid thread preview")
        return CodexThreadTitle(name, preview)

    def set_thread_name(self, thread_identifier: str, name: str) -> None:
        self.request("thread/name/set", {"threadId": thread_identifier, "name": name})
