import json
from dataclasses import replace
from pathlib import Path

from cycle_commands import CommandResult
from cycle_configuration import DARWIN_BACKGROUND_ISOLATION, CycleConfiguration
from cycle_decision import decide
from cycle_jobs import activation_command, rebuild_running, validation_command
from cycle_operator import operator_idle
from cycle_validation_worker import validate_revision
from steward_cycle_facts_fixtures import READY_TO_ACTIVATE
from test_steward_cycle_records_and_worker import configuration_in

REVISION = "a" * 40
CYCLE = ["python3", "steward_cycle.py"]


def darwin_configuration_in(state_directory: Path, **changes) -> CycleConfiguration:
    return replace(
        configuration_in(state_directory),
        entrypoint=None,
        configuration_attribute="darwinConfigurations.mac.system",
        idle_marker=None,
        job_isolation=DARWIN_BACKGROUND_ISOLATION,
        **changes,
    )


class ProcessListRunner:
    def __init__(self, output: str):
        self.output = output

    def run(self, arguments, directory, timeout_seconds):
        return CommandResult(0, self.output)


def test_linux_jobs_run_in_scopes_named_for_the_memory_bound(tmp_path):
    configuration = configuration_in(tmp_path)

    validation = validation_command(configuration, REVISION, 1, CYCLE)
    activation = activation_command(configuration, REVISION, CYCLE)

    assert validation[:6] == [
        "systemd-run",
        "--user",
        "--scope",
        "--quiet",
        "--collect",
        "--unit=steward-validate-aaaaaaaa",
    ]
    assert "--unit=steward-activation-aaaaaaaa" in activation
    assert activation[-4:] == [
        "rebuild",
        "--override-input",
        "dotfiles",
        configuration.pinned_repository_reference(REVISION),
    ]


def test_darwin_jobs_hold_a_lock_and_validate_at_background_priority(tmp_path):
    configuration = darwin_configuration_in(tmp_path)

    validation = validation_command(configuration, REVISION, 2, CYCLE)
    activation = activation_command(configuration, REVISION, CYCLE)

    lock = str(tmp_path / "jobs" / "steward-validate-aaaaaaaa.lock")
    assert validation[:6] == [*CYCLE, "run-job", "--lock", lock, "--"]
    assert validation[6:8] == ["taskpolicy", "-b"]
    assert activation[-2:] == ["--", "rebuild"]


def test_darwin_validation_builds_the_pinned_repository_directly(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    configuration = darwin_configuration_in(tmp_path)
    captured = {}

    def build(arguments, directory, log_path):
        captured["arguments"] = arguments
        log_path.write_text("")
        return 0, "/nix/store/darwin-system\n"

    record = validate_revision(configuration, None, REVISION, 1, build=build)

    assert "--override-input" not in captured["arguments"]
    assert captured["arguments"][-1] == (
        f"git+file:///home/user/.dotfiles?submodules=1&rev={REVISION}"
        "#darwinConfigurations.mac.system"
    )
    assert record["status"] == "green"
    assert record["entrypoint_head"] == ""


def test_darwin_settings_need_no_runtime_directory(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "repository": "/Users/user/.dotfiles",
                "entrypoint": None,
                "configuration_attribute": "darwinConfigurations.mac.system",
                "state_directory": "/Users/user/state",
                "idle_marker_name": None,
                "operator_idle_required": False,
                "job_isolation": DARWIN_BACKGROUND_ISOLATION,
                "inbox_directory": "/Users/user/inbox",
                "peers_file": "/Users/user/peers.json",
                "nix_binary": "/run/current-system/sw/bin/nix",
                "rebuild_command": "/nix/store/aaa-rebuild/bin/rebuild",
            }
        )
    )

    configuration = CycleConfiguration.from_settings(settings, {}, dry_run=False)

    assert configuration.entrypoint is None
    assert configuration.idle_marker is None
    assert not configuration.operator_idle_required


def test_darwin_idle_comes_from_the_human_interface_idle_time(tmp_path):
    configuration = darwin_configuration_in(tmp_path)
    away = ProcessListRunner('    | |   "HIDIdleTime" = 960000000000\n')
    present = ProcessListRunner('    | |   "HIDIdleTime" = 4000000000\n')

    assert operator_idle(configuration, away)
    assert not operator_idle(configuration, present)
    assert operator_idle(replace(configuration, operator_idle_required=False), present)


def test_an_unpinned_activation_waits_for_a_clean_working_tree():
    facts = replace(
        READY_TO_ACTIVATE, activation_reads_working_tree=True, tracked_dirty=True
    )

    assert decide(facts).action == "wait"
    assert decide(replace(facts, tracked_dirty=False)).action == "activate"


def test_a_running_rebuild_is_recognized_by_its_executable(tmp_path):
    store_executable = tmp_path / "store" / "aaa-rebuild" / "bin" / "rebuild"
    store_executable.parent.mkdir(parents=True)
    store_executable.write_text("")
    profile_link = tmp_path / "profile" / "bin" / "rebuild"
    profile_link.parent.mkdir(parents=True)
    profile_link.symlink_to(store_executable)
    idle = ProcessListRunner(
        f"bash -c cd ~/.dotfiles && rebuild\nvim notes {store_executable}\n"
    )

    assert not rebuild_running(idle, tmp_path)
    assert rebuild_running(ProcessListRunner(f"bash {profile_link}\n"), tmp_path)
    assert rebuild_running(ProcessListRunner(f"{store_executable} --x\n"), tmp_path)
