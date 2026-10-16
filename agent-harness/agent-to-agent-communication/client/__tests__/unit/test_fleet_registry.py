"""Synthetic inventories and transports; no live agents or model inference."""

import copy
import json
import os
import sys

import pytest
from a2a_cli.fleet import operations
from a2a_cli.fleet.cli import command_fleet
from a2a_cli.fleet.registry import Registry, normalize
from a2a_cli.__main__ import build_argument_parser


@pytest.fixture
def registry(tmp_path):
    import itertools

    ticks = itertools.count(1000000)
    registry = Registry(tmp_path / "registry.sqlite3", clock=lambda: next(ticks) / 1000)
    registry.confirm_host("test-host", "local", "fixture:host-confirmed")
    yield registry
    registry.close()


def inventory(session="conversation-1", state="idle", name="peer"):
    return (
        {name: {"name": name, "paneId": "w1:p1", "harness": "codex"}},
        {
            "result": {
                "snapshot": {
                    "agents": [
                        {
                            "pane_id": "w1:p1",
                            "agent": "codex",
                            "agent_status": state,
                            "interactive_ready": True,
                            "launch_pending": False,
                            "agent_session": {"kind": "id", "value": session},
                            "tab_id": "t1",
                            "workspace_id": "w1",
                        }
                    ]
                }
            }
        },
    )


def observe(registry, at=999, **kwargs):
    return registry.ingest(
        "test-host", *inventory(**kwargs), at, "fixture:snapshot", "live"
    )


class FakeTransport:
    def __init__(
        self,
        session="conversation-1",
        state="idle",
        task_state="working",
        fail_send=False,
    ):
        self.calls = []
        self.session = session
        self.state = state
        self.task_state = task_state
        self.fail_send = fail_send

    def __call__(self, host, command, timeout):
        self.calls.append(command)
        assert timeout <= 10
        directory, snapshot = inventory(session=self.session, state=self.state)
        if command[:2] == ["a2a", "list"]:
            return json.dumps(directory)
        if command[:3] == ["herdr", "api", "snapshot"]:
            return json.dumps(snapshot)
        if command[:2] == ["a2a", "send"]:
            if self.fail_send:
                raise operations.ObservationError("unreachable")
            return "remote-task-1\n"
        if command[:2] == ["a2a", "status"]:
            return json.dumps(
                {
                    "id": "remote-task-1",
                    "state": self.task_state,
                    "output": "sensitive output deliberately never retained",
                }
            )
        raise AssertionError(command)


def send(registry, transport, request="intent-1", **kwargs):
    return operations.dispatch(
        registry,
        request,
        "test-host",
        "w1:p1",
        "conversation-1",
        "dot",
        "task:review",
        kwargs.get("prompt", "Read the approved task brief."),
        transport,
    )


def test_persistence_and_cached_read_does_not_claim_live(tmp_path):
    path = tmp_path / "state" / "registry.sqlite3"
    first = Registry(path, clock=lambda: 1000)
    first.confirm_host("test-host", "local", "fixture:confirmed")
    observe(first)
    first.assign("test-host", "w1:p1", "conversation-1", "dot", "task:work")
    first.close()
    second = Registry(path, clock=lambda: 1100)
    try:
        row = second.status()["agents"][0]
        assert row["view"] == "cached" and row["fresh"]
        assert row["owner"] == "dot" and row["age_seconds"] == 101
        assert os.stat(path).st_mode & 0o777 == 0o600
    finally:
        second.close()


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
    old, new = rows["conversation-1"], rows["conversation-2"]
    assert old["present"] is False and old["owner"] == "dot"
    assert new["present"] and new["owner"] is None


def test_disappearance_is_not_task_failure(registry):
    observe(registry, at=998)
    registry.ingest(
        "test-host", {}, {"result": {"snapshot": {"agents": []}}}, 999, "fixture:empty"
    )
    row = registry.status()["agents"][0]
    assert not row["present"] and row["state"] == "idle"


def test_invalid_inventory_does_not_erase_evidence(registry):
    observe(registry)
    with pytest.raises(ValueError, match="snapshot"):
        registry.ingest("test-host", {}, {}, 1000, "fixture:malformed")
    assert registry.status()["agents"][0]["present"]


def test_duplicate_and_inconsistent_inventory_are_refused():
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"].append(
        copy.deepcopy(snapshot["result"]["snapshot"]["agents"][0])
    )
    with pytest.raises(ValueError, match="duplicate"):
        normalize(directory, snapshot)
    with pytest.raises(ValueError, match="disagree"):
        normalize(directory, {"result": {"snapshot": {"agents": []}}})


def test_path_sessions_are_never_opened_or_retained(registry):
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"][0]["agent_session"] = {
        "kind": "path",
        "value": "/secret/session",
    }
    registry.ingest("test-host", directory, snapshot, 999, "fixture:path")
    row = registry.status()["agents"][0]
    assert row["session_id"] is None
    assert "session_identity_unavailable" in row["blockers"]
    assert "/secret" not in json.dumps(registry.status())


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


def test_process_crash_after_reservation_survives_reopen(registry):
    observe(registry)
    registry.reserve(
        "intent-1",
        "test-host",
        "w1:p1",
        "conversation-1",
        "dot",
        "task:review",
        "Read the approved task brief.",
    )
    transport = FakeTransport()
    assert send(registry, transport)["state"] == "dispatching"
    assert not transport.calls


@pytest.mark.parametrize("state", ["working", "blocked", "unknown", "done"])
def test_nonidle_dispatch_is_refused(registry, state):
    transport = FakeTransport(state=state)
    with pytest.raises(ValueError, match="idle"):
        send(registry, transport)
    assert all(c[:2] != ["a2a", "send"] for c in transport.calls)


def test_changed_conversation_is_refused_before_send(registry):
    observe(registry)
    transport = FakeTransport(session="conversation-2")
    with pytest.raises(ValueError, match="idle"):
        send(registry, transport)
    assert all(c[:2] != ["a2a", "send"] for c in transport.calls)


def test_imported_metadata_cannot_authorize_dispatch(registry):
    registry.ingest("test-host", *inventory(), 999, "fixture:import")
    with pytest.raises(ValueError, match="live"):
        registry.reserve(
            "intent",
            "test-host",
            "w1:p1",
            "conversation-1",
            "dot",
            "task:work",
            "Do it",
        )


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


def test_remote_quoting_and_security_options():
    argv = operations.command_argv(
        {"transport": "confirmed-peer"},
        ["a2a", "send", "w1:p1", "literal $(touch /tmp/nope) ' text"],
    )
    assert argv[-2] == "confirmed-peer"
    assert "StrictHostKeyChecking=yes" in argv
    assert "ClearAllForwardings=yes" in argv
    import shlex

    assert shlex.split(argv[-1])[-1] == "literal $(touch /tmp/nope) ' text"


def test_transport_bounds_real_local_child_output_and_time():
    # Real local Python children, not live fleet commands or inference.
    assert (
        operations.run(
            {"transport": "local"}, [sys.executable, "-c", "print('ok')"], timeout=2
        ).strip()
        == "ok"
    )
    with pytest.raises(operations.ObservationError):
        operations.run(
            {"transport": "local"},
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.05,
        )
    with pytest.raises(operations.ObservationError, match="failed"):
        operations.run(
            {"transport": "local"},
            [sys.executable, "-c", "print('x'*3000000)"],
            timeout=2,
        )


def test_cli_cached_status_bypasses_a2a_discovery(tmp_path, capsys, monkeypatch):
    from a2a_cli import __main__

    def forbidden(*args, **kwargs):
        raise AssertionError("cached status must not perform discovery")

    monkeypatch.setattr(__main__, "read_agent_directory", forbidden)
    monkeypatch.setattr(
        sys, "argv", ["a2a", "fleet", "--db", str(tmp_path / "db"), "status"]
    )
    assert __main__.main() == 0
    assert json.loads(capsys.readouterr().out)["agents"] == []


def test_cli_ingest_marks_cached_and_is_quiet(tmp_path, capsys):
    db = tmp_path / "db"
    parser = build_argument_parser()
    assert (
        command_fleet(
            parser.parse_args(
                [
                    "fleet",
                    "--db",
                    str(db),
                    "confirm-host",
                    "test-host",
                    "--transport",
                    "local",
                    "--evidence",
                    "fixture:confirmed",
                ]
            )
        )
        == 0
    )
    directory, snapshot = inventory()
    source = tmp_path / "metadata.json"
    source.write_text(
        json.dumps(
            {
                "a2a": directory,
                "herdr": snapshot,
                "observed_at": 999,
                "evidence": "fixture:import",
            }
        )
    )
    assert (
        command_fleet(
            parser.parse_args(
                ["fleet", "--db", str(db), "ingest", "test-host", str(source)]
            )
        )
        == 0
    )
    assert capsys.readouterr().out == ""
    r = Registry(db)
    try:
        assert r.status()["agents"][0]["source"] == "cached"
    finally:
        r.close()


def test_registry_refuses_public_or_symlink_database(tmp_path):
    path = tmp_path / "db"
    path.touch(mode=0o644)
    with pytest.raises(ValueError, match="0600"):
        Registry(path)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(OSError):
        Registry(link)


def test_idle_without_readiness_is_not_dispatchable(registry):
    directory, snapshot = inventory()
    snapshot["result"]["snapshot"]["agents"][0].pop("interactive_ready")
    registry.ingest("test-host", directory, snapshot, 999, "fixture:unready", "live")
    with pytest.raises(ValueError, match="readiness"):
        registry.reserve(
            "intent-1",
            "test-host",
            "w1:p1",
            "conversation-1",
            "dot",
            "task:work",
            "Do it",
        )
    assert registry.status()["agents"][0]["delivery_readiness"] == "unverified"


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


def test_two_connections_cannot_reserve_the_same_pane(registry):
    observe(registry)
    path = registry.db.execute("PRAGMA database_list").fetchone()[2]
    second = Registry(path, clock=lambda: 1000)
    try:
        registry.reserve(
            "intent-1", "test-host", "w1:p1", "conversation-1", "dot", "task:a", "Work"
        )
        with pytest.raises(ValueError, match="unresolved"):
            second.reserve(
                "intent-2",
                "test-host",
                "w1:p1",
                "conversation-1",
                "dot",
                "task:b",
                "Work",
            )
    finally:
        second.close()
