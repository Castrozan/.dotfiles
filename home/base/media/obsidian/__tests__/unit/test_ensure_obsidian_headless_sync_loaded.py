import os
import re
import subprocess
from pathlib import Path

OBSIDIAN_MODULE_DIRECTORY = Path(__file__).resolve().parents[2]
RECONCILE_SCRIPT_PATH = (
    OBSIDIAN_MODULE_DIRECTORY / "scripts" / "ensure-obsidian-headless-sync-loaded.sh"
)
HEADLESS_SYNC_MODULE = OBSIDIAN_MODULE_DIRECTORY / "headless-sync.nix"
LAUNCHCTL_ASSIGNMENT = re.compile(r'^LAUNCHCTL="[^"]+"$', re.M)


def script_source() -> str:
    return RECONCILE_SCRIPT_PATH.read_text()


def declared_label() -> str:
    matched = re.search(r'Label = "([^"]+)"', HEADLESS_SYNC_MODULE.read_text())
    assert matched, "the module no longer declares a launchd label"
    return matched.group(1)


def build_launchctl_recorder(
    directory: Path, print_exit_code: int
) -> tuple[Path, Path]:
    call_log = directory / "launchctl-calls.log"
    recorder = directory / "launchctl-recorder"
    recorder.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$@" >> "{call_log}"\n'
        f'if [ "$1" = "print" ]; then exit {print_exit_code}; fi\n'
        "exit 0\n"
    )
    recorder.chmod(0o755)
    return recorder, call_log


def build_failing_launchctl_recorder(directory: Path) -> tuple[Path, Path]:
    call_log = directory / "launchctl-calls.log"
    recorder = directory / "launchctl-recorder"
    recorder.write_text(f'#!/usr/bin/env bash\necho "$@" >> "{call_log}"\nexit 1\n')
    recorder.chmod(0o755)
    return recorder, call_log


def script_with_launchctl_replaced_by(recorder: Path, directory: Path) -> Path:
    source = script_source()
    assert LAUNCHCTL_ASSIGNMENT.search(source), (
        "the script no longer assigns LAUNCHCTL on its own line, so this test can no "
        "longer redirect it at a recorder and would silently stop exercising anything"
    )
    instrumented = directory / "ensure-obsidian-headless-sync-loaded.sh"
    instrumented.write_text(
        LAUNCHCTL_ASSIGNMENT.sub(f'LAUNCHCTL="{recorder}"', source, count=1)
    )
    return instrumented


def deploy_agent_plist(home_directory: Path) -> None:
    launch_agents = home_directory / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True)
    (launch_agents / f"{declared_label()}.plist").write_text("<plist/>\n")


def run_reconcile_script(instrumented: Path, home_directory: Path):
    return subprocess.run(
        ["bash", str(instrumented)],
        capture_output=True,
        text=True,
        timeout=10,
        env={"HOME": str(home_directory), "PATH": os.environ["PATH"]},
    )


def recorded_subcommands(call_log: Path) -> list[str]:
    if not call_log.exists():
        return []
    return [line.split()[0] for line in call_log.read_text().splitlines() if line]


def test_the_reconcile_script_targets_the_label_the_module_declares():
    assert RECONCILE_SCRIPT_PATH.is_file()
    assert declared_label() in script_source(), (
        f"the self-heal script reconciles a different label than the declared "
        f"{declared_label()}, so it would never revive the real agent"
    )


def test_it_exits_quietly_when_no_agent_plist_is_deployed(tmp_path):
    recorder, call_log = build_launchctl_recorder(tmp_path, print_exit_code=1)
    instrumented = script_with_launchctl_replaced_by(recorder, tmp_path)

    completed = run_reconcile_script(instrumented, tmp_path)

    assert completed.returncode == 0
    assert completed.stdout == "", (
        "with no plist deployed there is nothing to reconcile, so the script must stay silent"
    )
    assert recorded_subcommands(call_log) == [], (
        "with no plist deployed the script must not touch launchd at all"
    )


def test_an_already_registered_agent_is_left_alone(tmp_path):
    home_directory = tmp_path / "home"
    home_directory.mkdir()
    deploy_agent_plist(home_directory)
    recorder, call_log = build_launchctl_recorder(tmp_path, print_exit_code=0)
    instrumented = script_with_launchctl_replaced_by(recorder, tmp_path)

    completed = run_reconcile_script(instrumented, home_directory)

    assert completed.returncode == 0
    assert recorded_subcommands(call_log) == ["print"], (
        "a healthy agent must cost one probe and nothing else, otherwise every "
        "rebuild would bounce a running sync"
    )


def test_a_vanished_agent_is_booted_out_then_enabled_then_bootstrapped(tmp_path):
    home_directory = tmp_path / "home"
    home_directory.mkdir()
    deploy_agent_plist(home_directory)
    recorder, call_log = build_launchctl_recorder(tmp_path, print_exit_code=1)
    instrumented = script_with_launchctl_replaced_by(recorder, tmp_path)

    completed = run_reconcile_script(instrumented, home_directory)

    assert completed.returncode == 0
    assert recorded_subcommands(call_log) == [
        "print",
        "bootout",
        "enable",
        "bootstrap",
        "kickstart",
    ], (
        "bootstrapping a disabled label fails with EIO 5 and bootstrapping over a "
        "stale registration collides, so the order has to be bootout, enable, "
        "bootstrap, kickstart or the agent silently stays dead"
    )


def test_the_reconcile_runs_to_completion_even_when_every_call_fails(tmp_path):
    home_directory = tmp_path / "home"
    home_directory.mkdir()
    deploy_agent_plist(home_directory)
    recorder, call_log = build_failing_launchctl_recorder(tmp_path)
    instrumented = script_with_launchctl_replaced_by(recorder, tmp_path)

    completed = run_reconcile_script(instrumented, home_directory)

    assert completed.returncode == 0, (
        "a launchctl call that fails on an already-correct state must not abort the "
        "reconcile, or the agent is left unloaded"
    )
    assert recorded_subcommands(call_log) == [
        "print",
        "bootout",
        "enable",
        "bootstrap",
        "kickstart",
    ], "every step has to be attempted even after an earlier one fails"
