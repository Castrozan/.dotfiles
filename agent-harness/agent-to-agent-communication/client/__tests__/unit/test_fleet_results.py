import json
import pytest
from a2a_cli.fleet import operations
from fleet_test_support import FakeTransport, send


def test_reported_completion_needs_separate_verification(registry):
    transport = FakeTransport(task_state="completed")
    send(registry, transport)
    job = operations.result(registry, "intent-1", transport)
    assert job["state"] == "reported_completed"
    assert "sensitive output" not in json.dumps(registry.status())
    with pytest.raises(ValueError, match="unresolved"):
        send(registry, transport, request="intent-2")
    assert (
        registry.verify("intent-1", "artifact:commit-and-test-log")["state"]
        == "completed"
    )
    assert send(registry, transport, request="intent-2")["state"] == "dispatched"


def test_task_status_unavailable_does_not_mean_task_failed(registry):
    transport = FakeTransport()
    send(registry, transport)

    def missing_task(host, command, timeout):
        if command[:2] == ["a2a", "status"]:
            raise operations.ObservationError("failed")
        return transport(host, command, timeout)

    job = operations.result(registry, "intent-1", missing_task)
    assert job["state"] == "dispatched" and job["blocker"] == "status_unavailable"


def test_completion_cannot_be_manually_invented_before_remote_report(registry):
    send(registry, FakeTransport())
    with pytest.raises(ValueError, match="reported"):
        registry.verify("intent-1", "artifact:wrong")


def test_correlation_is_sent_and_survives_lost_remote_record(registry):
    transport = FakeTransport()
    send(registry, transport)
    assert transport.calls[-1][3].startswith("[dot-fleet:intent-1] ")

    def lost_record(host, command, timeout):
        if command[:2] == ["a2a", "status"]:
            raise operations.ObservationError("failed")
        return transport(host, command, timeout)

    job = operations.result(registry, "intent-1", lost_record)
    assert job["correlation"] == "[dot-fleet:intent-1]"
    assert job["remote_task_id"] == "remote-task-1" and job["state"] == "dispatched"
    job = registry.reconcile(
        "intent-1", "artifact:independently-checked-result", outcome="completed"
    )
    assert job["state"] == "completed"


def test_recovered_receipt_is_delivery_not_completion(registry):
    send(registry, FakeTransport(fail_send=True))
    job = registry.reconcile(
        "intent-1", "fixture:exact-ACK-and-task-id", remote_task_id="recovered-1"
    )
    assert job["state"] == "dispatched" and job["delivery_evidence"]
    with pytest.raises(ValueError, match="overwrite"):
        registry.reconcile("intent-1", "fixture:other", remote_task_id="other-id")


def test_stale_poll_cannot_regress_verified_completion(registry):
    send(registry, FakeTransport())
    registry.reconcile("intent-1", "artifact:verified", outcome="completed")
    assert registry.update_job("intent-1", "working")["state"] == "completed"


def test_independent_failed_artifact_can_settle_reported_completion(registry):
    transport = FakeTransport(task_state="completed")
    send(registry, transport)
    operations.result(registry, "intent-1", transport)
    job = registry.reconcile(
        "intent-1", "artifact:failed-acceptance-tests", outcome="failed"
    )
    assert (
        job["state"] == "failed"
        and job["evidence"] == "artifact:failed-acceptance-tests"
    )


def test_result_of_proved_non_submission_is_cached_terminal(registry):
    send(registry, FakeTransport(fail_send=True))
    registry.reconcile(
        "intent-1", "fixture:explicit-rejection", outcome="not_submitted"
    )
    transport = FakeTransport()
    assert (
        operations.result(registry, "intent-1", transport)["state"] == "not_submitted"
    )
    assert not transport.calls
