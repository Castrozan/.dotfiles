import json
import pytest
from a2a_cli.fleet.registry import DispatchIntent, Observation
from fleet_test_support import inventory, observe, FakeTransport, send


def test_dispatch_persists_receipt_and_never_means_completed(registry):
    transport = FakeTransport()
    job = send(registry, transport)
    assert job["state"] == "dispatched" and job["remote_task_id"] == "remote-task-1"
    assert transport.calls[-1][2] == "w1:p1"
    assert "Read the approved" not in json.dumps(registry.status())


def test_same_intent_never_resubmits_and_changed_intent_is_refused(registry):
    transport = FakeTransport()
    send(registry, transport)
    count = len(transport.calls)
    assert send(registry, transport)["state"] == "dispatched"
    assert len(transport.calls) == count
    with pytest.raises(ValueError, match="different dispatch"):
        send(registry, transport, prompt="Different instruction")
    assert len(transport.calls) == count


def test_receipt_loss_is_uncertain_and_prevents_second_task(registry):
    transport = FakeTransport(fail_send=True)
    assert send(registry, transport)["state"] == "uncertain"
    with pytest.raises(ValueError, match="unresolved"):
        send(registry, transport, request="intent-2")
    assert len([c for c in transport.calls if c[:2] == ["a2a", "send"]]) == 1


@pytest.mark.parametrize("state", ["working", "blocked", "unknown", "done"])
def test_nonidle_dispatch_is_refused(registry, state):
    transport = FakeTransport(state=state)
    with pytest.raises(ValueError, match="idle"):
        send(registry, transport)
    assert all((c[:2] != ["a2a", "send"] for c in transport.calls))


def test_changed_conversation_is_refused_before_send(registry):
    observe(registry)
    transport = FakeTransport(session="conversation-2")
    with pytest.raises(ValueError, match="idle"):
        send(registry, transport)
    assert all((c[:2] != ["a2a", "send"] for c in transport.calls))


def test_imported_metadata_cannot_authorize_dispatch(registry):
    registry.ingest("test-host", Observation(*inventory(), 999, "fixture:import"))
    with pytest.raises(ValueError, match="live"):
        registry.reserve(
            DispatchIntent(
                "intent",
                "test-host",
                "w1:p1",
                "conversation-1",
                "dot",
                "task:work",
                "Do it",
            )
        )


def test_idle_without_readiness_is_not_dispatchable(registry):
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"][0].pop("interactive_ready")
    registry.ingest(
        "test-host", Observation(directory, snapshot, 999, "fixture:unready", "live")
    )
    with pytest.raises(ValueError, match="readiness"):
        registry.reserve(
            DispatchIntent(
                "intent-1",
                "test-host",
                "w1:p1",
                "conversation-1",
                "dot",
                "task:work",
                "Do it",
            )
        )
    assert registry.status()["agents"][0]["delivery_readiness"] == "unverified"
