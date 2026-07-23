import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import yaml

from coached_fixtures import (
    E2E_WORKSPACE_PARENT,
    build_coach_prompt,
    load_compliance_skill_body,
    setup_workspace,
)
from coached_models import CoachedSessionResult
from coached_scoring import (
    calculate_nps_from_tool_sequence_and_workspace,
    parse_tool_sequence,
)
from e2e_herdr import (
    create_isolated_herdr_tab_for_test,
    destroy_test_tab,
    herdr_server_is_reachable,
    launch_claude_in_herdr_pane,
)
from e2e_herdr_io import (
    capture_full_terminal_output,
    send_prompt_to_claude_session,
    wait_for_claude_to_become_ready,
    wait_for_response_completion,
)

COACHED_TAB_LABEL_PREFIX = "coached-"


def run_coached_scenario(
    scenario_path: Path,
    model: str = "opus",
) -> CoachedSessionResult:
    scenario = yaml.safe_load(scenario_path.read_text())
    scenario_name = scenario["name"]

    if not herdr_server_is_reachable():
        return CoachedSessionResult(
            scenario_name=scenario_name,
            initial_nps=0,
            coached_nps=0,
            improvement=0,
            initial_tool_sequence=[],
            coached_tool_sequence=[],
            coach_findings="",
            duration_seconds=0,
            error="herdr server not reachable",
        )

    E2E_WORKSPACE_PARENT.mkdir(parents=True, exist_ok=True)
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", scenario_name)[:30]
    timestamp = int(time.time())
    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"coached-{sanitized}-",
            dir=E2E_WORKSPACE_PARENT,
        )
    )
    worker_tab_label = f"{COACHED_TAB_LABEL_PREFIX}worker-{timestamp}"
    timeout = scenario.get("timeout", 300)
    worker_handle: dict[str, str] = {}

    try:
        setup_workspace(scenario, workspace)
        start_time = time.time()

        worker_handle = create_isolated_herdr_tab_for_test(worker_tab_label, workspace)
        if not worker_handle:
            raise RuntimeError("herdr tab could not be created")
        worker_pane_id = worker_handle["pane_id"]
        launch_claude_in_herdr_pane(worker_pane_id, model)

        if not wait_for_claude_to_become_ready(worker_pane_id):
            return CoachedSessionResult(
                scenario_name=scenario_name,
                initial_nps=0,
                coached_nps=0,
                improvement=0,
                initial_tool_sequence=[],
                coached_tool_sequence=[],
                coach_findings="",
                duration_seconds=time.time() - start_time,
                error="Worker failed to start",
            )

        prompt_text = scenario.get("prompt", "")
        send_prompt_to_claude_session(worker_pane_id, prompt_text)
        wait_for_response_completion(worker_pane_id, timeout)

        initial_output = capture_full_terminal_output(worker_pane_id)
        initial_tools = parse_tool_sequence(initial_output)
        initial_nps = calculate_nps_from_tool_sequence_and_workspace(
            initial_tools,
            workspace,
            scenario,
        )

        compliance_body = load_compliance_skill_body()
        coach_prompt = build_coach_prompt(initial_tools, workspace)
        coach_result = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                "haiku",
                "--system-prompt",
                compliance_body,
                coach_prompt,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=workspace,
        )
        coach_findings = coach_result.stdout.strip()

        initial_fail_count = coach_findings.count("FAIL:")
        initial_nps = max(0, initial_nps - (initial_fail_count * 15))

        has_failures = initial_fail_count > 0

        if has_failures:
            correction_prompt = (
                "The compliance reviewer found these "
                "violations in your work:\n\n"
                f"{coach_findings}\n\n"
                "Fix each FAIL finding now."
            )
            send_prompt_to_claude_session(worker_pane_id, correction_prompt)
            wait_for_response_completion(worker_pane_id, timeout)

        coached_output = capture_full_terminal_output(worker_pane_id)
        coached_tools = parse_tool_sequence(coached_output)
        coached_workspace_nps = calculate_nps_from_tool_sequence_and_workspace(
            coached_tools,
            workspace,
            scenario,
        )

        if has_failures:
            coached_coach_prompt = build_coach_prompt(coached_tools, workspace)
            coached_coach_result = subprocess.run(
                [
                    "claude",
                    "-p",
                    "--model",
                    "haiku",
                    "--system-prompt",
                    compliance_body,
                    coached_coach_prompt,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=workspace,
            )
            coached_findings = coached_coach_result.stdout.strip()
            coached_fail_count = coached_findings.count("FAIL:")
            coached_nps = max(
                0,
                coached_workspace_nps - (coached_fail_count * 15),
            )
            coach_findings += "\n\n--- AFTER CORRECTION ---\n" + coached_findings
        else:
            coached_nps = coached_workspace_nps

        duration = time.time() - start_time

        return CoachedSessionResult(
            scenario_name=scenario_name,
            initial_nps=initial_nps,
            coached_nps=coached_nps,
            improvement=coached_nps - initial_nps,
            initial_tool_sequence=initial_tools,
            coached_tool_sequence=coached_tools,
            coach_findings=coach_findings,
            duration_seconds=duration,
        )

    finally:
        if worker_handle:
            destroy_test_tab(worker_handle["tab_id"])
        shutil.rmtree(workspace, ignore_errors=True)
