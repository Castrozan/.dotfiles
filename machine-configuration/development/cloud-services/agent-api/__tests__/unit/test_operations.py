import uuid

import pytest

from agent_api.contract import CapabilityError, OperationRequest
from agent_api.operations import OperationStore


def request(text="hello"):
    return OperationRequest("web.extract", {"url": "https://example.com/" + text}, 30)


def test_success_replays_and_changed_input_conflicts(tmp_path):
    store = OperationStore(tmp_path / "state")
    operation_id = str(uuid.uuid4())
    assert store.claim(operation_id, request()) is None
    result = store.finish(operation_id, "succeeded", {"text": "hello"})
    assert store.claim(operation_id, request()) == result
    with pytest.raises(CapabilityError, match="operation_conflict"):
        store.claim(operation_id, request("changed"))


def test_failed_and_running_operations_cannot_dispatch_again(tmp_path):
    store = OperationStore(tmp_path / "state")
    operation_id = str(uuid.uuid4())
    store.claim(operation_id, request())
    with pytest.raises(CapabilityError, match="operation_incomplete"):
        store.claim(operation_id, request())
    store.finish(operation_id, "failed", {"error": "provider_failed"})
    with pytest.raises(CapabilityError, match="operation_incomplete"):
        store.claim(operation_id, request())


def test_concurrent_claim_and_capacity_are_shared_between_connections(tmp_path):
    first = OperationStore(tmp_path / "state")
    second = OperationStore(tmp_path / "state")
    operation_id = str(uuid.uuid4())
    first.claim(operation_id, request())
    with pytest.raises(CapabilityError, match="operation_incomplete"):
        second.claim(operation_id, request())
    second.claim(str(uuid.uuid4()), request())
    with pytest.raises(CapabilityError, match="capacity_exceeded"):
        first.claim(str(uuid.uuid4()), request())


def test_expired_operation_releases_capacity_without_resubmission(tmp_path):
    store = OperationStore(tmp_path / "state")
    operation_id = str(uuid.uuid4())
    store.claim(operation_id, request())
    with store.connect() as connection:
        connection.execute("UPDATE operations SET expires_at = 0")
    assert store.inspect(operation_id)["status"] == "interrupted"
    with pytest.raises(CapabilityError, match="operation_incomplete"):
        store.claim(operation_id, request())


def test_artifact_tampering_blocks_successful_replay(tmp_path):
    store = OperationStore(tmp_path / "state")
    operation_id = str(uuid.uuid4())
    store.claim(operation_id, request())
    artifact = store.directory(operation_id) / "asset.txt"
    artifact.write_text("original")
    store.finish(operation_id, "succeeded", {"text": "hello"})
    artifact.write_text("changed")
    with pytest.raises(CapabilityError, match="artifact_changed"):
        store.claim(operation_id, request())
