import pytest

from agent_session import codex_launcher_migration as migration
from agent_session import codex_migration_readiness


def test_idle_shell_baseline_uses_pane_read_and_resumes_once(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    result = migration.migrate(plan, commands, directory / "attempt")
    assert result["status"] == "continuation-submitted"
    assert commands.launches == commands.continuations == 1
    assert all(command[1:3] != ["agent", "read"] for command in commands.calls)
    launch = next(
        command for command in commands.calls if command[1:3] == ["pane", "run"]
    )
    assert launch[-2:] == ["resume", plan["thread_identifier"]]
    assert clock.value >= 1.0


def test_orphan_birth_stops_before_any_launch_and_records_observation(
    prepared_migration, monkeypatch
):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setattr(
        migration,
        "process_birth",
        lambda pid: {"start_ticks": 200, "state": "S", "parent": 1815}
        if pid == 20
        else None,
    )
    result = migration.migrate(plan, commands, directory / "orphan-attempt")
    assert result["status"] == "failed"
    assert result["phase"] == "await-old-processes"
    assert result["remaining_old_processes"][0]["pid"] == 20
    assert result["remaining_old_processes"][0]["observed"]["parent"] == 1815
    assert commands.launches == commands.continuations == 0
    assert clock.value == pytest.approx(30.0)


def test_reused_pid_and_zombie_do_not_block_release(prepared_migration, monkeypatch):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setattr(
        migration,
        "process_birth",
        lambda pid: {
            "start_ticks": 101 if pid == 10 else 200,
            "state": "S" if pid == 10 else "Z",
            "parent": 1,
        },
    )
    assert (
        migration.migrate(plan, commands, directory / "attempt")["status"]
        == "continuation-submitted"
    )
    assert commands.launches == 1


def test_wrong_resumed_thread_refuses_continuation(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    commands.thread = "another-thread"
    result = migration.migrate(plan, commands, directory / "wrong-thread")
    assert result["status"] == "failed"
    assert commands.continuations == 0


def test_old_birth_cannot_be_accepted_as_replacement(prepared_migration, monkeypatch):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setattr(
        codex_migration_readiness,
        "inspect_new_processes",
        lambda *arguments: {
            "pids": {"server": 20},
            "births": {"server": {"start_ticks": 200}},
        },
    )
    result = migration.migrate(plan, commands, directory / "stale-runtime")
    assert result["status"] == "failed"
    assert commands.launches == 1 and commands.continuations == 0


def test_busy_continuation_is_not_retried(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    commands.fail_continuation = True
    result = migration.migrate(plan, commands, directory / "busy-continuation")
    assert result["status"] == "failed"
    assert commands.launches == commands.continuations == 1


def test_launch_failure_is_not_retried(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    commands.fail_launch = True
    assert (
        migration.migrate(plan, commands, directory / "launch-failure")["status"]
        == "failed"
    )
    assert commands.launches == 1 and commands.continuations == 0


def test_missing_replacement_times_out_without_continuation(
    prepared_migration, monkeypatch
):
    plan, commands, directory, clock = prepared_migration

    def not_ready(*arguments):
        raise LookupError("server not available")

    monkeypatch.setattr(codex_migration_readiness, "inspect_new_processes", not_ready)
    result = migration.migrate(plan, commands, directory / "not-ready")
    assert result["status"] == "failed"
    assert clock.value == pytest.approx(60.0)
    assert commands.launches == 1 and commands.continuations == 0


def test_missing_retained_pane_refuses_launch(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    commands.pane = "different-pane"
    assert (
        migration.migrate(plan, commands, directory / "missing-pane")["status"]
        == "failed"
    )
    assert commands.launches == 0
