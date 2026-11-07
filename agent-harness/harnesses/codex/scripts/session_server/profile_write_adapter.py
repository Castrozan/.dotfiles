from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import tempfile
import threading
import time

import tomlkit


BATCH_WRITE_METHOD = "config/batchWrite"


@dataclass(frozen=True)
class PendingProfileWrite:
    settings: dict[str, str | None]
    profile_only: bool


def partition_profile_edits(edits):
    settings = {}
    native_edits = []
    for edit in edits:
        if (
            edit.get("keyPath") in {"model", "model_reasoning_effort"}
            and (edit.get("value") is None or isinstance(edit.get("value"), str))
            and edit.get("mergeStrategy") in {"replace", "upsert"}
        ):
            settings[edit["keyPath"]] = edit.get("value")
        else:
            native_edits.append(edit)
    return settings, native_edits


def try_exclusive_lock(lock) -> bool:
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    return True


def acquire_exclusive_lock(lock) -> None:
    deadline = time.monotonic() + 1.0
    while not try_exclusive_lock(lock):
        if time.monotonic() >= deadline:
            raise TimeoutError("Codex profile remained locked for 1s")
        time.sleep(0.02)


def apply_profile_settings(configuration, settings: dict[str, str | None]) -> None:
    for key, value in settings.items():
        if value is None:
            configuration.pop(key, None)
        else:
            configuration[key] = value


def save_profile_settings(profile_path: Path, settings: dict[str, str | None]) -> None:
    with profile_path.with_suffix(".toml.lock").open("a") as lock:
        acquire_exclusive_lock(lock)
        configuration = tomlkit.parse(profile_path.read_text())
        apply_profile_settings(configuration, settings)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=profile_path.parent, delete=False
        ) as output:
            temporary_path = Path(output.name)
            try:
                os.fchmod(output.fileno(), profile_path.stat().st_mode & 0o777)
                output.write(configuration.as_string())
                output.flush()
                os.fsync(output.fileno())
                os.replace(temporary_path, profile_path)
            finally:
                temporary_path.unlink(missing_ok=True)


class CodexProfileWriteAdapter:
    def __init__(self, profile_path: Path):
        self.profile_path = profile_path
        self.pending_writes = {}
        self.pending_lock = threading.Lock()

    def prepare_request(self, frame: str | bytes) -> str | bytes:
        try:
            request = json.loads(frame)
        except ValueError:
            return frame
        if not isinstance(request, dict) or request.get("method") not in {
            BATCH_WRITE_METHOD,
            "config/value/write",
        }:
            return frame
        parameters = request.get("params") or {}
        target_path = parameters.get("filePath")
        if target_path and Path(target_path).resolve() not in {
            self.profile_path,
            self.profile_path.parent / "config.toml",
        }:
            return frame
        edits = (
            parameters.get("edits", [])
            if request["method"] == BATCH_WRITE_METHOD
            else [parameters]
        )
        settings, native_edits = partition_profile_edits(edits)
        if not settings:
            return frame
        with self.pending_lock:
            self.pending_writes[request["id"]] = PendingProfileWrite(
                settings, not native_edits
            )
        request["method"] = BATCH_WRITE_METHOD
        request["params"] = {
            key: value
            for key, value in parameters.items()
            if key in {"filePath", "expectedVersion", "reloadUserConfig"}
        }
        request["params"]["edits"] = native_edits
        if target_path and Path(target_path).resolve() == self.profile_path:
            request["params"].pop("filePath", None)
        return json.dumps(request)

    def finish_response(self, frame: str | bytes) -> str | bytes:
        with self.pending_lock:
            if not self.pending_writes:
                return frame
        response = json.loads(frame)
        with self.pending_lock:
            pending = self.pending_writes.pop(response.get("id"), None)
        if pending is None or "result" not in response:
            return frame
        try:
            save_profile_settings(self.profile_path, pending.settings)
        except (OSError, ValueError) as error:
            return json.dumps(
                {
                    "id": response["id"],
                    "error": {
                        "code": -32603,
                        "message": f"Could not save Codex profile: {error}",
                    },
                }
            )
        if pending.profile_only:
            response["result"]["filePath"] = str(self.profile_path)
        return json.dumps(response)
