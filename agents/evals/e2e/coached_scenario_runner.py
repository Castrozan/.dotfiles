import re
import shutil
import tempfile
import time
from pathlib import Path

import yaml

from coached_compliance_reviewer import (
    count_compliance_failures,
    nps_after_compliance_penalty,
    review_tool_sequence_for_compliance,
)
from coached_fixtures import (
    E2E_WORKSPACE_PARENT,
    load_compliance_skill_body,
    setup_workspace,
)
from coached_models import CoachedSessionResult, failed_coached_session
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
CORRECTION_PROMPT_TEMPLATE = (
    "The compliance reviewer found these violations in your work:\n\n"
    "{findings}\n\n"
    "Fix each FAIL finding now."
)


def deliver_prompt_and_wait(pane_id: str, prompt_text: str, timeout: float) -> bool:
    if not send_prompt_to_claude_session(pane_id, prompt_text):
        return False
    return wait_for_response_completion(
        pane_id, capture_full_terminal_output(pane_id), timeout
    )


def run_coached_scenario(
    scenario_path: Path,
    model: str = "opus",
) -> CoachedSessionResult:
    scenario = yaml.safe_load(scenario_path.read_text())
    scenario_name = scenario["name"]

    if not herdr_server_is_reachable():
        return failed_coached_session(scenario_name, 0, "herdr server not reachable")

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
            return failed_coached_session(
                scenario_name, time.time() - start_time, "Worker failed to start"
            )

        if not deliver_prompt_and_wait(
            worker_pane_id, scenario.get("prompt", ""), timeout
        ):
            return failed_coached_session(
                scenario_name,
                time.time() - start_time,
                "Worker never completed the initial prompt",
            )

        initial_tools = parse_tool_sequence(
            capture_full_terminal_output(worker_pane_id)
        )
        initial_workspace_nps = calculate_nps_from_tool_sequence_and_workspace(
            initial_tools,
            workspace,
            scenario,
        )

        compliance_body = load_compliance_skill_body()
        coach_findings = review_tool_sequence_for_compliance(
            compliance_body, initial_tools, workspace
        )
        initial_failure_count = count_compliance_failures(coach_findings)
        initial_nps = nps_after_compliance_penalty(
            initial_workspace_nps, initial_failure_count
        )
        has_failures = initial_failure_count > 0

        if has_failures:
            deliver_prompt_and_wait(
                worker_pane_id,
                CORRECTION_PROMPT_TEMPLATE.format(findings=coach_findings),
                timeout,
            )

        coached_tools = parse_tool_sequence(
            capture_full_terminal_output(worker_pane_id)
        )
        coached_workspace_nps = calculate_nps_from_tool_sequence_and_workspace(
            coached_tools,
            workspace,
            scenario,
        )

        if has_failures:
            coached_findings = review_tool_sequence_for_compliance(
                compliance_body, coached_tools, workspace
            )
            coached_nps = nps_after_compliance_penalty(
                coached_workspace_nps, count_compliance_failures(coached_findings)
            )
            coach_findings += "\n\n--- AFTER CORRECTION ---\n" + coached_findings
        else:
            coached_nps = coached_workspace_nps

        return CoachedSessionResult(
            scenario_name=scenario_name,
            initial_nps=initial_nps,
            coached_nps=coached_nps,
            improvement=coached_nps - initial_nps,
            initial_tool_sequence=initial_tools,
            coached_tool_sequence=coached_tools,
            coach_findings=coach_findings,
            duration_seconds=time.time() - start_time,
        )

    finally:
        if worker_handle:
            destroy_test_tab(worker_handle["tab_id"])
        shutil.rmtree(workspace, ignore_errors=True)
