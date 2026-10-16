import os
import sys
import pytest
from a2a_cli.fleet.registry import Registry, DispatchIntent
from fleet_test_support import observe, FakeTransport, send


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
        assert os.stat(path).st_mode & 511 == 384
    finally:
        second.close()


def test_process_crash_after_reservation_survives_reopen(registry):
    observe(registry)
    registry.reserve(
        DispatchIntent(
            "intent-1",
            "test-host",
            "w1:p1",
            "conversation-1",
            "dot",
            "task:review",
            "Read the approved task brief.",
        )
    )
    transport = FakeTransport()
    assert send(registry, transport)["state"] == "dispatching"
    assert not transport.calls


def test_registry_refuses_public_or_symlink_database(tmp_path):
    path = tmp_path / "db"
    path.touch(mode=420)
    with pytest.raises(ValueError, match="0600"):
        Registry(path)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(OSError):
        Registry(link)


def test_two_connections_cannot_reserve_the_same_pane(registry):
    observe(registry)
    path = registry.db.execute("PRAGMA database_list").fetchone()[2]
    second = Registry(path, clock=lambda: 1000)
    try:
        registry.reserve(
            DispatchIntent(
                "intent-1",
                "test-host",
                "w1:p1",
                "conversation-1",
                "dot",
                "task:a",
                "Work",
            )
        )
        with pytest.raises(ValueError, match="unresolved"):
            second.reserve(
                DispatchIntent(
                    "intent-2",
                    "test-host",
                    "w1:p1",
                    "conversation-1",
                    "dot",
                    "task:b",
                    "Work",
                )
            )
    finally:
        second.close()


def test_newer_schema_is_refused_without_migration_or_erasure(tmp_path):
    import sqlite3

    path = tmp_path / "db"
    r = Registry(path)
    r.db.execute("PRAGMA user_version=99")
    r.close()
    with pytest.raises(ValueError, match="schema"):
        Registry(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 99


def test_reservation_survives_abrupt_process_exit_and_prevents_replay(registry):
    import subprocess
    from pathlib import Path

    observe(registry)
    path = registry.db.execute("PRAGMA database_list").fetchone()[2]
    package = Path(__file__).resolve().parents[2] / "scripts"
    script = "import os,sys\nfrom a2a_cli.fleet.registry import Registry, DispatchIntent\nr=Registry(sys.argv[1],clock=lambda:1000)\nr.reserve(DispatchIntent('intent-1','test-host','w1:p1','conversation-1','dot','task:review','Read the approved task brief.'))\nos._exit(0)\n"
    subprocess.run(
        [sys.executable, "-c", script, path],
        env={**os.environ, "PYTHONPATH": str(package)},
        check=True,
        timeout=5,
    )
    reopened = Registry(path, clock=lambda: 1000)
    try:
        transport = FakeTransport()
        assert send(reopened, transport)["state"] == "dispatching"
        assert not transport.calls
    finally:
        reopened.close()
