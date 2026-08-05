import atexit
import json
import subprocess
from pathlib import Path

E2E_TAB_LABEL_PREFIX = "e2e-test-"
HERDR_COMMAND_TIMEOUT_SECONDS = 15

ACTIVE_TEST_TAB_IDS: list[str] = []


def run_herdr_command(
    arguments: list[str], timeout_seconds: float = HERDR_COMMAND_TIMEOUT_SECONDS
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["herdr"] + arguments,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return subprocess.CompletedProcess(
            arguments, returncode=1, stdout="", stderr=""
        )


def herdr_result_payload(completed: subprocess.CompletedProcess) -> dict:
    if completed.returncode != 0 or not completed.stdout.strip():
        return {}
    try:
        return json.loads(completed.stdout).get("result", {})
    except json.JSONDecodeError:
        return {}


def herdr_server_is_reachable() -> bool:
    return run_herdr_command(["tab", "list"]).returncode == 0


def create_isolated_herdr_tab_for_test(
    tab_label: str, working_directory: Path
) -> dict[str, str]:
    payload = herdr_result_payload(
        run_herdr_command(
            [
                "tab",
                "create",
                "--cwd",
                str(working_directory),
                "--label",
                tab_label,
                "--no-focus",
            ]
        )
    )
    tab_id = payload.get("tab", {}).get("tab_id")
    pane_id = payload.get("root_pane", {}).get("pane_id")
    if not tab_id or not pane_id:
        return {}
    ACTIVE_TEST_TAB_IDS.append(tab_id)
    return {"tab_id": tab_id, "pane_id": pane_id}


def launch_claude_in_herdr_pane(pane_id: str, model: str) -> None:
    run_herdr_command(
        [
            "pane",
            "run",
            pane_id,
            f"claude --model {model} --dangerously-skip-permissions",
        ]
    )


def destroy_test_tab(tab_id: str) -> None:
    run_herdr_command(["tab", "close", tab_id])
    if tab_id in ACTIVE_TEST_TAB_IDS:
        ACTIVE_TEST_TAB_IDS.remove(tab_id)


def close_orphaned_test_tabs() -> None:
    for tab_id in list(ACTIVE_TEST_TAB_IDS):
        destroy_test_tab(tab_id)


atexit.register(close_orphaned_test_tabs)
