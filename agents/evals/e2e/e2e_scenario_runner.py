import shutil
import tempfile
import time
from pathlib import Path

from e2e_assertions_workspace import run_e2e_assertions
from e2e_models import E2eScenarioResult, TerminalSessionTrace
from e2e_scoring import calculate_e2e_experience_score
from e2e_herdr import (
    E2E_TAB_LABEL_PREFIX,
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
from e2e_trace import build_terminal_session_trace
from e2e_workspace import (
    E2E_WORKSPACE_PARENT,
    load_scenario,
    sanitize_name_for_session,
    save_debug_capture,
    setup_e2e_scenario_workspace,
)


def run_e2e_scenario(
    scenario_path: Path,
    model: str = "haiku",
    dry_run: bool = False,
    debug_capture: bool = False,
    claude_ab_mode: str = "inline",
) -> E2eScenarioResult:
    scenario = load_scenario(scenario_path)
    scenario_name = scenario["name"]

    if dry_run:
        return E2eScenarioResult(
            scenario_name=scenario_name,
            passed=True,
            assertion_results=[],
            trace=TerminalSessionTrace(),
            workspace_directory=None,
            duration_seconds=0,
        )

    if not herdr_server_is_reachable():
        return E2eScenarioResult(
            scenario_name=scenario_name,
            passed=False,
            assertion_results=[],
            trace=TerminalSessionTrace(),
            workspace_directory=None,
            duration_seconds=0,
            error="herdr server not reachable",
        )

    sanitized = sanitize_name_for_session(scenario_name)
    timestamp = int(time.time())
    tab_label = f"{E2E_TAB_LABEL_PREFIX}{sanitized}-{timestamp}"
    E2E_WORKSPACE_PARENT.mkdir(parents=True, exist_ok=True)
    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"e2e-{sanitized}-",
            dir=E2E_WORKSPACE_PARENT,
        )
    )
    timeout = scenario.get("timeout", 300)
    tab_handle: dict[str, str] = {}

    try:
        setup_e2e_scenario_workspace(scenario, workspace, claude_ab_mode)

        tab_handle = create_isolated_herdr_tab_for_test(tab_label, workspace)
        if not tab_handle:
            return E2eScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=TerminalSessionTrace(),
                workspace_directory=workspace,
                duration_seconds=0,
                error="herdr tab could not be created",
            )
        pane_id = tab_handle["pane_id"]

        launch_claude_in_herdr_pane(pane_id, model)

        if not wait_for_claude_to_become_ready(pane_id):
            return E2eScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=TerminalSessionTrace(),
                workspace_directory=workspace,
                duration_seconds=0,
                error="Claude failed to start (agent never reported idle)",
            )

        prompts = scenario.get("prompts", [])
        if not prompts:
            single_prompt = scenario.get("prompt", "")
            if single_prompt:
                prompts = [single_prompt]

        start_time = time.time()

        for prompt_text in prompts:
            delivered = send_prompt_to_claude_session(pane_id, prompt_text)
            completed = delivered and wait_for_response_completion(
                pane_id, timeout_seconds=timeout
            )
            if not completed:
                failure_reason = (
                    f"Timed out after {timeout}s"
                    if delivered
                    else "prompt could not be delivered to the herdr pane"
                )
                raw_output = capture_full_terminal_output(pane_id)
                duration = time.time() - start_time
                trace = build_terminal_session_trace(
                    raw_output, duration, timed_out=True
                )

                if debug_capture:
                    save_debug_capture(scenario_name, raw_output)

                assertion_results = run_e2e_assertions(
                    trace,
                    scenario.get("assertions", {}),
                    workspace,
                )
                experience_score = calculate_e2e_experience_score(
                    trace, assertion_results, workspace
                )

                return E2eScenarioResult(
                    scenario_name=scenario_name,
                    passed=False,
                    assertion_results=assertion_results,
                    trace=trace,
                    workspace_directory=workspace,
                    duration_seconds=duration,
                    experience_score=experience_score,
                    error=failure_reason,
                )

        raw_output = capture_full_terminal_output(pane_id)
        duration = time.time() - start_time

        if debug_capture:
            save_debug_capture(scenario_name, raw_output)

        trace = build_terminal_session_trace(raw_output, duration, timed_out=False)

        assertion_results = run_e2e_assertions(
            trace,
            scenario.get("assertions", {}),
            workspace,
        )
        all_passed = all(a.passed for a in assertion_results)
        experience_score = calculate_e2e_experience_score(
            trace, assertion_results, workspace
        )

        return E2eScenarioResult(
            scenario_name=scenario_name,
            passed=all_passed,
            assertion_results=assertion_results,
            trace=trace,
            workspace_directory=workspace,
            duration_seconds=duration,
            experience_score=experience_score,
        )

    finally:
        if tab_handle:
            destroy_test_tab(tab_handle["tab_id"])
        shutil.rmtree(workspace, ignore_errors=True)
