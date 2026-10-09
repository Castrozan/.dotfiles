import hashlib
import json
from pathlib import Path

import pytest

from agent_session import codex_launcher_migration as migration


class FixtureClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        return self.value

    def sleep(self, duration):
        self.value += duration


class FixtureCommands:
    def __init__(self, pane, thread):
        self.pane = pane
        self.thread = thread
        self.calls = []
        self.launches = 0
        self.continuations = 0
        self.fail_launch = False
        self.fail_continuation = False
        self.configuration = None

    def herdr(self, label, arguments, deadline=None):
        self.calls.append(arguments)
        if arguments[:2] == ["pane", "process-info"]:
            return {
                "process_info": {
                    "pane_id": self.pane,
                    "shell_pid": 70,
                    "foreground_process_group_id": 70,
                }
            }
        if arguments[:2] == ["pane", "get"]:
            return {
                "pane": {
                    "pane_id": self.pane,
                    "agent_session": {"agent": "codex", "value": self.thread},
                }
            }
        raise AssertionError(arguments)

    def run(self, label, arguments, timeout=5.0):
        self.calls.append(arguments)
        if arguments[1:3] == ["agent", "read"]:
            raise RuntimeError("no recognized agent in idle shell")
        if arguments[1:3] == ["pane", "read"]:
            return (
                "shell prompt"
                if not self.launches
                else "Ask Codex to do anything\ngpt-6 50% context left"
            )
        if arguments[1:3] == ["pane", "run"]:
            self.launches += 1
            if self.fail_launch:
                raise RuntimeError("pane run returned status1")
            return ""
        raise AssertionError(arguments)

    def send(self, pane, message):
        self.continuations += 1
        if self.fail_continuation:
            raise RuntimeError("peer is already working")
        return {"target": pane, "task_identifier": "fixture-only"}


@pytest.fixture
def prepared_migration(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    clock = FixtureClock()
    monkeypatch.setattr(migration.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(migration.time, "sleep", clock.sleep)
    configuration = tmp_path / "config.toml"
    configuration.write_text("installed configuration")
    plan = {
        "pane_identifier": "wT:p6G",
        "thread_identifier": "01a11e3f-d21e-7e42-b9be-350c32c32379",
        "launcher": "/nix/store/fixture-codex-private-session",
        "upstream_binary": "/nix/store/fixture-codex/bin/codex",
        "preferences": "/nix/store/fixture-preferences",
        "configuration_sources": {
            str(configuration): hashlib.sha256(configuration.read_bytes()).hexdigest()
        },
        "source_hashes": {},
        "rollout": str(tmp_path / "rollout.jsonl"),
        "old_processes": [
            {"pid": 10, "start_ticks": 100},
            {"pid": 20, "start_ticks": 200},
        ],
        "continuation": "Resume this exact fixture thread.",
    }
    monkeypatch.setenv("HERDR_PANE_ID", plan["pane_identifier"])
    monkeypatch.setenv("CODEX_THREAD_ID", plan["thread_identifier"])
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    commands = FixtureCommands(plan["pane_identifier"], plan["thread_identifier"])
    monkeypatch.setattr(
        migration, "validate_package", lambda plan: {"package": plan["launcher"]}
    )
    monkeypatch.setattr(migration, "validate_rollout", lambda plan: None)
    monkeypatch.setattr(migration, "process_birth", lambda pid: None)
    monkeypatch.setattr(
        migration,
        "inspect_new_processes",
        lambda process_info, pane, package, plan: {
            "pids": {"launcher": 30, "server": 31, "client": 32},
            "births": {
                "launcher": {"start_ticks": 300},
                "server": {"start_ticks": 310},
                "client": {"start_ticks": 320},
            },
        },
    )
    return plan, commands, tmp_path, clock


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


def test_existing_attempt_is_never_overwritten(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    attempt = directory / "existing"
    attempt.mkdir()
    old = attempt / "result.json"
    old.write_text("original historical failure")
    with pytest.raises(FileExistsError):
        migration.migrate(plan, commands, attempt)
    assert old.read_text() == "original historical failure"
    assert not commands.calls


def test_separate_attempts_retain_both_results(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    migration.migrate(plan, commands, directory / "first")
    first = (directory / "first/result.json").read_bytes()
    migration.migrate(plan, commands, directory / "second")
    assert (directory / "first/result.json").read_bytes() == first
    assert (directory / "first/old-processes.json").exists()
    assert (directory / "second/old-processes.json").exists()


def test_wrong_resumed_thread_refuses_continuation(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    commands.thread = "another-thread"
    result = migration.migrate(plan, commands, directory / "wrong-thread")
    assert result["status"] == "failed"
    assert commands.continuations == 0


def test_old_birth_cannot_be_accepted_as_replacement(prepared_migration, monkeypatch):
    plan, commands, directory, clock = prepared_migration
    monkeypatch.setattr(
        migration,
        "inspect_new_processes",
        lambda *arguments: {
            "pids": {"server": 20},
            "births": {"server": {"start_ticks": 200}},
        },
    )
    result = migration.migrate(plan, commands, directory / "stale-runtime")
    assert result["status"] == "failed"
    assert commands.launches == 1 and commands.continuations == 0


def test_configuration_drift_stops_before_launch(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    Path(next(iter(plan["configuration_sources"]))).write_text("old MCP configuration")
    result = migration.migrate(plan, commands, directory / "config-drift")
    assert result["status"] == "failed"
    assert commands.launches == 0


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

    monkeypatch.setattr(migration, "inspect_new_processes", not_ready)
    result = migration.migrate(plan, commands, directory / "not-ready")
    assert result["status"] == "failed"
    assert clock.value == pytest.approx(60.0)
    assert commands.launches == 1 and commands.continuations == 0


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


def test_missing_retained_pane_refuses_launch(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    commands.pane = "different-pane"
    assert (
        migration.migrate(plan, commands, directory / "missing-pane")["status"]
        == "failed"
    )
    assert commands.launches == 0


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
    migration.validate_rollout(
        {"rollout": str(path), "thread_identifier": "exact-thread"}
    )
    with pytest.raises(ValueError, match="saved rollout thread mismatch"):
        migration.validate_rollout(
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
