import shutil
import tempfile
import time
from pathlib import Path

from e2e_assertions import run_e2e_assertions
from e2e_harness_profiles import scenario_harness_profile
from e2e_models import E2eScenarioResult, TerminalSessionTrace
from e2e_scoring import (
    calculate_e2e_experience_score,
    check_minimum_e2e_experience_score,
)
from e2e_herdr import (
    E2E_TAB_LABEL_PREFIX,
    create_isolated_herdr_tab_for_test,
    destroy_test_tab,
    herdr_server_is_reachable,
    launch_agent_in_herdr_pane,
)
from e2e_herdr_io import (
    capture_full_terminal_output,
    wait_for_agent_to_become_ready,
)
from e2e_scenario_steps import run_scenario_step, scenario_steps
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
    instruction_placement_mode: str = "inline",
) -> E2eScenarioResult:
    scenario = load_scenario(scenario_path)
    scenario_name = scenario["name"]
    profile = scenario_harness_profile(scenario)

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
        setup_e2e_scenario_workspace(
            scenario, workspace, profile, instruction_placement_mode
        )

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

        launch_agent_in_herdr_pane(pane_id, profile, model, workspace)

        if not wait_for_agent_to_become_ready(pane_id, profile):
            return E2eScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=TerminalSessionTrace(),
                workspace_directory=workspace,
                duration_seconds=0,
                error=f"{profile.name} never became ready to accept a prompt",
            )

        start_time = time.time()

        for scenario_step in scenario_steps(scenario):
            failure_reason = run_scenario_step(pane_id, scenario_step, profile, timeout)
            if failure_reason:
                raw_output = capture_full_terminal_output(pane_id)
                duration = time.time() - start_time
                trace = build_terminal_session_trace(
                    raw_output, duration, timed_out=True, workspace=workspace
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

        trace = build_terminal_session_trace(
            raw_output, duration, timed_out=False, workspace=workspace
        )

        assertion_results = run_e2e_assertions(
            trace,
            scenario.get("assertions", {}),
            workspace,
        )
        experience_score = calculate_e2e_experience_score(
            trace, assertion_results, workspace
        )
        if "minimum_experience_score" in scenario:
            assertion_results.append(
                check_minimum_e2e_experience_score(
                    experience_score, scenario["minimum_experience_score"]
                )
            )
        all_passed = all(assertion.passed for assertion in assertion_results)

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
