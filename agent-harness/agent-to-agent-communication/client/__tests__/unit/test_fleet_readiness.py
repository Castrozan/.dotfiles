"""Sanitized Herdr 0.9.1 field shape reported by fleet live acceptance.

The producer omits false launch_pending and interactive_ready values
(src/api/schema/agents.rs, serde default + skip_serializing_if=is_false).
Identifiers are synthetic; these tests perform no live dispatch.
"""

import pytest
from a2a_cli.fleet.registry import DispatchIntent, Observation
from fleet_test_support import FakeTransport, inventory, send


def test_omitted_false_launch_pending_allows_ready_dispatch(registry):
    _, snapshot = inventory()
    agent = snapshot["result"]["snapshot"]["agents"][0]
    assert "launch_pending" not in agent
    assert agent["interactive_ready"] is True
    assert send(registry, FakeTransport())["state"] == "dispatched"
    assert registry.status()["agents"][0]["launch_pending"] is False


@pytest.mark.parametrize("value", [False, True, None, 0, "false"])
def test_explicit_launch_pending_preserves_strict_readiness(registry, value):
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"][0]["launch_pending"] = value
    registry.ingest(
        "test-host", Observation(directory, snapshot, 999, "fixture:readiness", "live")
    )
    intent = DispatchIntent(
        "intent", "test-host", "w1:p1", "conversation-1", "dot", "task:work", "Do it"
    )
    if value is False:
        assert registry.reserve(intent)[1] is True
    else:
        with pytest.raises(ValueError, match="readiness"):
            registry.reserve(intent)
        assert registry.status()["jobs"] == []


@pytest.mark.parametrize("value", [False, None, "true"])
def test_omitted_pending_cannot_replace_interactive_readiness(registry, value):
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"][0]["interactive_ready"] = value
    registry.ingest(
        "test-host", Observation(directory, snapshot, 999, "fixture:unready", "live")
    )
    with pytest.raises(ValueError, match="readiness"):
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
    assert registry.status()["jobs"] == []
