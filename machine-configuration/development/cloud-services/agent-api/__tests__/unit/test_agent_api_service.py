import json
import uuid

import pytest

from agent_api.contract import CapabilityError, OperationRequest
from agent_api.service import CapabilityService


class RecordingExecutor:
    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def execute(self, directory, timeout_seconds):
        self.calls += 1
        if self.error:
            raise self.error
        return {
            "operation_id": json.loads((directory / "request.json").read_text())[
                "operation_id"
            ]
        }


def test_replay_does_not_start_another_worker(tmp_path):
    executor = RecordingExecutor()
    service = CapabilityService(tmp_path / "state", executor)
    operation_id = str(uuid.uuid4())
    request = OperationRequest("web.extract", {"url": "https://example.com"})
    result = service.run(operation_id, request)
    assert result == service.run(operation_id, request)
    assert executor.calls == 1


def test_deadline_failure_is_retained_and_never_resubmitted(tmp_path):
    executor = RecordingExecutor(CapabilityError("deadline_exceeded"))
    service = CapabilityService(tmp_path / "state", executor)
    operation_id = str(uuid.uuid4())
    request = OperationRequest("web.extract", {"url": "https://example.com"})
    with pytest.raises(CapabilityError, match="deadline_exceeded"):
        service.run(operation_id, request)
    assert service.store.inspect(operation_id)["result"]["error"] == "deadline_exceeded"
    with pytest.raises(CapabilityError, match="operation_incomplete"):
        service.run(operation_id, request)
    assert executor.calls == 1


def test_changed_local_file_conflicts_even_when_its_path_is_identical(tmp_path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"first")
    executor = RecordingExecutor()
    service = CapabilityService(tmp_path / "state", executor)
    operation_id = str(uuid.uuid4())
    request = OperationRequest("media.probe", {"path": str(source)})
    service.run(operation_id, request)
    source.write_bytes(b"second")
    with pytest.raises(CapabilityError, match="operation_conflict"):
        service.run(operation_id, request)
    assert executor.calls == 1


def test_missing_credentials_do_not_claim_an_operation(tmp_path, monkeypatch):
    from agent_api.providers import credentials

    monkeypatch.setenv("MONID_API_KEY", "")
    monkeypatch.setattr(credentials.Path, "home", lambda: tmp_path)
    service = CapabilityService(tmp_path / "state", RecordingExecutor())
    operation_id = str(uuid.uuid4())
    with pytest.raises(CapabilityError, match="missing_credentials"):
        service.run(
            operation_id, OperationRequest("monid.discover", {"query": "video"})
        )
    with pytest.raises(CapabilityError, match="operation_not_found"):
        service.store.inspect(operation_id)
