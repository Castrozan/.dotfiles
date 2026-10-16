import copy
import json
import pytest
from a2a_cli.fleet.registry import normalize, Observation
from fleet_test_support import inventory, empty_snapshot, observe


def test_host_confirmation_is_not_health(registry):
    assert registry.status()["hosts"][0]["observation"] == "unknown"
    assert registry.status()["hosts"][0]["last_seen"] is None


def test_unknown_hosts_and_remapping_are_refused(registry):
    with pytest.raises(ValueError, match="unconfirmed"):
        registry.host("invented-peer")
    with pytest.raises(ValueError, match="remapped"):
        registry.confirm_host("test-host", "different-alias", "fixture:bad")
    with pytest.raises(ValueError, match="SSH alias"):
        registry.confirm_host("other", "-oProxyCommand=evil", "fixture:bad")


def test_stale_and_future_evidence(registry):
    observe(registry, at=500)
    assert registry.status()["agents"][0]["fresh"] is False
    with pytest.raises(ValueError, match="future"):
        observe(registry, at=2000)
    assert not observe(registry, at=400, state="working")
    assert registry.status()["agents"][0]["state"] == "idle"


def test_unreachable_preserves_last_known_agent_state(registry):
    observe(registry)
    registry.failure("test-host", "unreachable")
    status = registry.status()
    assert status["hosts"][0]["observation"] == "unreachable"
    assert status["agents"][0]["state"] == "idle"
    assert status["agents"][0]["last_seen"] == 999
    registry.failure("test-host", "failed")
    assert registry.status()["hosts"][0]["observation"] == "failed"


def test_session_rotation_retains_history_without_inheriting_ownership(registry):
    observe(registry, at=998)
    registry.assign("test-host", "w1:p1", "conversation-1", "dot", "old-task")
    observe(registry, at=999, session="conversation-2")
    rows = {r["session_id"]: r for r in registry.status()["agents"]}
    old, new = (rows["conversation-1"], rows["conversation-2"])
    assert old["present"] is False and old["owner"] == "dot"
    assert new["present"] and new["owner"] is None


def test_disappearance_is_not_task_failure(registry):
    observe(registry, at=998)
    registry.ingest(
        "test-host", Observation({}, empty_snapshot(), 999, "fixture:empty")
    )
    row = registry.status()["agents"][0]
    assert not row["present"] and row["state"] == "idle"


def test_invalid_inventory_does_not_erase_evidence(registry):
    observe(registry)
    with pytest.raises(ValueError, match="snapshot"):
        registry.ingest("test-host", Observation({}, {}, 1000, "fixture:malformed"))
    assert registry.status()["agents"][0]["present"]


def test_duplicate_and_inconsistent_inventory_are_refused():
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"].append(
        copy.deepcopy(snapshot["result"]["snapshot"]["agents"][0])
    )
    with pytest.raises(ValueError, match="duplicate"):
        normalize(directory, snapshot)
    with pytest.raises(ValueError, match="disagree"):
        normalize(directory, empty_snapshot())


def test_path_sessions_are_never_opened_or_retained(registry):
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"][0]["agent_session"] = {
        "kind": "path",
        "value": "/secret/session",
    }
    registry.ingest("test-host", Observation(directory, snapshot, 999, "fixture:path"))
    row = registry.status()["agents"][0]
    assert row["session_id"] is None
    assert "session_identity_unavailable" in row["blockers"]
    assert "/secret" not in json.dumps(registry.status())


def test_partial_snapshot_cannot_retire_all_agents(registry):
    observe(registry)
    with pytest.raises(ValueError, match="snapshot"):
        registry.ingest(
            "test-host",
            Observation(
                {}, {"result": {"snapshot": {"agents": []}}}, 1000, "fixture:partial"
            ),
        )
    assert registry.status()["agents"][0]["present"]
