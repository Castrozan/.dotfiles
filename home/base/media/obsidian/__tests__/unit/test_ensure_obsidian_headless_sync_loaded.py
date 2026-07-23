import os
import re
import subprocess
from pathlib import Path

OBSIDIAN_MODULE_DIRECTORY = Path(__file__).resolve().parents[2]
RECONCILE_SCRIPT_PATH = (
    OBSIDIAN_MODULE_DIRECTORY / "scripts" / "ensure-obsidian-headless-sync-loaded.sh"
)
HEADLESS_SYNC_MODULE = OBSIDIAN_MODULE_DIRECTORY / "headless-sync.nix"


def script_source() -> str:
    return RECONCILE_SCRIPT_PATH.read_text()


def line_index_of(fragment: str) -> int:
    for index, line in enumerate(script_source().splitlines()):
        if fragment in line:
            return index
    return -1


def test_the_reconcile_script_targets_the_label_the_module_declares():
    assert RECONCILE_SCRIPT_PATH.is_file()
    declared_label = re.search(r'Label = "([^"]+)"', HEADLESS_SYNC_MODULE.read_text())
    assert declared_label, "the module no longer declares a launchd label"
    assert declared_label.group(1) in script_source(), (
        f"the self-heal script reconciles a different label than the declared "
        f"{declared_label.group(1)}, so it would never revive the real agent"
    )


def test_it_exits_quietly_when_no_agent_plist_is_deployed(tmp_path):
    completed = subprocess.run(
        ["bash", str(RECONCILE_SCRIPT_PATH)],
        capture_output=True,
        text=True,
        timeout=10,
        env={"HOME": str(tmp_path), "PATH": os.environ["PATH"]},
    )
    assert completed.returncode == 0
    assert completed.stdout == "", (
        "with no plist deployed there is nothing to reconcile, so the script must stay silent"
    )


def test_the_label_is_enabled_before_it_is_bootstrapped():
    enable_index = line_index_of("enable ")
    bootstrap_index = line_index_of("bootstrap ")
    assert enable_index != -1 and bootstrap_index != -1
    assert enable_index < bootstrap_index, (
        "bootstrapping a disabled label fails with EIO 5, so the label has to be "
        "enabled first or the agent silently stays dead"
    )


def test_the_stale_registration_is_booted_out_before_the_label_is_enabled():
    bootout_index = line_index_of("bootout ")
    enable_index = line_index_of("enable ")
    assert bootout_index != -1
    assert bootout_index < enable_index, (
        "a half-registered label has to be booted out before enable and bootstrap, "
        "otherwise the bootstrap collides with the stale registration"
    )


def test_every_reconcile_call_tolerates_its_own_failure():
    reconcile_lines = [
        line.strip()
        for line in script_source().splitlines()
        if '"$LAUNCHCTL"' in line and "print" not in line
    ]
    assert reconcile_lines, (
        "the reconcile sequence disappeared, so this guard is vacuous"
    )
    for line in reconcile_lines:
        assert line.endswith("|| true"), (
            f"'{line}' can fail on an already-correct state, and without a tolerant "
            f"exit it would abort the rest of the reconcile sequence"
        )


def test_the_script_does_not_abort_on_the_first_failing_command():
    assert "set -euo pipefail" not in script_source(), (
        "errexit would abort the reconcile at the first launchctl call that fails on "
        "an already-correct state, leaving the agent unloaded"
    )
    assert "set -uo pipefail" in script_source()
