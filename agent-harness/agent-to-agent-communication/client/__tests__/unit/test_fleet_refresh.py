import json
import pytest
from a2a_cli.fleet import operations
from a2a_cli.fleet.registry import Registry
from fleet_test_support import observe, FakeTransport


def test_refresh_is_explicit_bounded_and_reports_only_successes_live(registry):
    transport = FakeTransport()
    live = operations.refresh(registry, ["test-host"], transport)
    assert len(transport.calls) == 2
    assert registry.status(live)["agents"][0]["view"] == "live"
    assert registry.status()["agents"][0]["view"] == "cached"
    with pytest.raises(ValueError, match="four|4"):
        operations.refresh(registry, [str(i) for i in range(5)], transport)
    assert len(transport.calls) == 2


def test_refresh_validates_all_hosts_before_any_call(registry):
    transport = FakeTransport()
    with pytest.raises(ValueError, match="unconfirmed"):
        operations.refresh(registry, ["test-host", "missing"], transport)
    assert not transport.calls


def test_refresh_budget_exhaustion_never_calls_transport(registry):
    transport = FakeTransport()
    assert operations.refresh(registry, ["test-host"], transport, budget=0) == []
    assert not transport.calls
    assert registry.status()["hosts"][0]["observation"] == "unreachable"


def test_refresh_failure_preserves_evidence(registry):
    observe(registry)

    def malformed(*args, **kwargs):
        return "not json"

    assert operations.refresh(registry, ["test-host"], malformed) == []
    assert registry.status()["hosts"][0]["observation"] == "failed"
    assert registry.status()["agents"][0]["last_seen"] == 999


def test_event_invalidates_without_promoting_identity_or_freshness(registry):
    observe(registry)
    registry.event(
        "test-host",
        {"event": "pane.agent_status_changed", "data": {"agent_status": "idle"}},
        "fixture:existing-subscription",
    )
    view = registry.status()
    assert not view["agents"][0]["fresh"]
    assert view["agents"][0]["last_seen"] == 999
    assert view["hosts"][0]["refresh_required"]
    operations.refresh(registry, ["test-host"], FakeTransport())
    assert registry.status()["agents"][0]["fresh"]


def test_unknown_event_does_not_mutate_registry(registry):
    observe(registry)
    with pytest.raises(ValueError, match="unsupported"):
        registry.event(
            "test-host",
            {"event": "pane.output_matched", "data": "private text"},
            "fixture:unsupported",
        )
    assert "private text" not in json.dumps(registry.status())
    assert registry.status()["agents"][0]["fresh"]


def test_offline_host_cached_query_after_failed_refresh(registry):
    observe(registry)

    def offline(*args, **kwargs):
        raise operations.ObservationError("unreachable")

    assert operations.refresh(registry, ["test-host"], offline) == []
    view = registry.status()
    assert view["hosts"][0]["observation"] == "unreachable"
    assert view["agents"][0]["view"] == "cached"
    assert view["agents"][0]["session_id"] == "conversation-1"


def test_lifecycle_envelope_invalidates_durably(registry):
    observe(registry)
    registry.event(
        "test-host",
        {"event": "pane_created", "data": {"pane": "untrusted"}},
        "fixture:herdr-event",
    )
    path = registry.db.execute("PRAGMA database_list").fetchone()[2]
    second = Registry(path, clock=lambda: 1000)
    try:
        assert second.status()["hosts"][0]["refresh_required"]
        assert not second.status()["agents"][0]["fresh"]
        assert "untrusted" not in json.dumps(second.status())
    finally:
        second.close()
