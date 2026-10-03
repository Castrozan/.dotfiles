import time
from pathlib import Path

from e2e.assertions.e2e_assertions import run_e2e_assertions
from e2e.sessions.e2e_models import E2eScenarioResult
from e2e.sessions.e2e_herdr_io import capture_full_terminal_output
from e2e.sessions.e2e_trace import build_terminal_session_trace
from e2e.sessions.e2e_workspace import save_debug_capture
from e2e_scoring import (
    calculate_e2e_experience_score,
    check_minimum_e2e_experience_score,
)


def failed_e2e_scenario_result(
    scenario: dict,
    scenario_name: str,
    pane_id: str,
    workspace: Path,
    start_time: float,
    failure_reason: str,
    debug_capture: bool,
) -> E2eScenarioResult:
    raw_output = capture_full_terminal_output(pane_id)
    duration = time.time() - start_time
    trace = build_terminal_session_trace(
        raw_output, duration, timed_out=True, workspace=workspace
    )
    if debug_capture:
        save_debug_capture(scenario_name, raw_output)
    assertion_results = run_e2e_assertions(
        trace, scenario.get("assertions", {}), workspace
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


def successful_e2e_scenario_result(
    scenario: dict,
    scenario_name: str,
    pane_id: str,
    workspace: Path,
    start_time: float,
    debug_capture: bool,
) -> E2eScenarioResult:
    raw_output = capture_full_terminal_output(pane_id)
    duration = time.time() - start_time
    if debug_capture:
        save_debug_capture(scenario_name, raw_output)
    trace = build_terminal_session_trace(
        raw_output, duration, timed_out=False, workspace=workspace
    )
    assertion_results = run_e2e_assertions(
        trace, scenario.get("assertions", {}), workspace
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
    return E2eScenarioResult(
        scenario_name=scenario_name,
        passed=all(assertion.passed for assertion in assertion_results),
        assertion_results=assertion_results,
        trace=trace,
        workspace_directory=workspace,
        duration_seconds=duration,
        experience_score=experience_score,
    )
