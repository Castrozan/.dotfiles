import hashlib
from agent_session import codex_launcher_migration as migration
from agent_session import codex_migration_inputs, codex_migration_readiness


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


def prepare_migration(tmp_path, monkeypatch):
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
        codex_migration_inputs,
        "validate_package",
        lambda plan: {"package": plan["launcher"]},
    )
    monkeypatch.setattr(codex_migration_inputs, "validate_rollout", lambda plan: None)
    monkeypatch.setattr(migration, "process_birth", lambda pid: None)
    monkeypatch.setattr(
        codex_migration_readiness,
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
