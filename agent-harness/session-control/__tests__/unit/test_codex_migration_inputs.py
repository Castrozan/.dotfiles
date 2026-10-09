import json
from pathlib import Path

import pytest

from agent_session import codex_launcher_migration as migration
from agent_session import codex_migration_inputs


def test_configuration_drift_stops_before_launch(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    Path(next(iter(plan["configuration_sources"]))).write_text("old MCP configuration")
    result = migration.migrate(plan, commands, directory / "config-drift")
    assert result["status"] == "failed"
    assert commands.launches == 0


def test_target_must_match_enclosing_pane(prepared_migration, monkeypatch):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setenv("HERDR_PANE_ID", "wT:peer")
    assert (
        migration.migrate(plan, commands, directory / "wrong-pane")["status"]
        == "failed"
    )
    assert not commands.calls


@pytest.mark.parametrize(
    "seed",
    [
        [],
        [{"pid": True, "start_ticks": 1}],
        [{"pid": 1, "start_ticks": 1}, {"pid": 1, "start_ticks": 2}],
    ],
)
def test_invalid_owned_seed_refuses_before_commands(prepared_migration, seed):
    plan, commands, directory, clock = prepared_migration
    plan["old_processes"] = seed
    assert (
        migration.migrate(plan, commands, directory / "bad-seed")["status"] == "failed"
    )
    assert not commands.calls


def test_configuration_change_during_old_exit_wait_refuses_launch(
    prepared_migration, monkeypatch
):
    plan, commands, directory, clock = prepared_migration

    def disappear(pid):
        Path(next(iter(plan["configuration_sources"]))).write_text(
            "configuration changed after preflight"
        )
        return None

    monkeypatch.setattr(migration, "process_birth", disappear)
    assert (
        migration.migrate(plan, commands, directory / "changed-config")["status"]
        == "failed"
    )
    assert commands.launches == 0


def test_rollout_requires_exact_persisted_session(tmp_path):
    path = tmp_path / "rollout.jsonl"
    path.write_text(
        json.dumps({"type": "session_meta", "payload": {"id": "exact-thread"}}) + "\n"
    )
    codex_migration_inputs.validate_rollout(
        {"rollout": str(path), "thread_identifier": "exact-thread"}
    )
    with pytest.raises(ValueError, match="saved rollout thread mismatch"):
        codex_migration_inputs.validate_rollout(
            {"rollout": str(path), "thread_identifier": "other-thread"}
        )


def test_wrong_inherited_thread_refuses_before_commands(
    prepared_migration, monkeypatch
):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setenv("CODEX_THREAD_ID", "different-thread")
    assert (
        migration.migrate(plan, commands, directory / "wrong-inherited-thread")[
            "status"
        ]
        == "failed"
    )
    assert not commands.calls


def test_managed_session_is_refused(prepared_migration, monkeypatch):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "fixture-managed-agent")
    assert (
        migration.migrate(plan, commands, directory / "managed")["status"] == "failed"
    )
    assert not commands.calls


def test_linux_procfs_is_required_before_any_command(prepared_migration, monkeypatch):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setattr("sys.platform", "darwin")
    result = migration.migrate(plan, commands, directory / "unsupported-platform")
    assert result["status"] == "failed"
    assert not commands.calls
