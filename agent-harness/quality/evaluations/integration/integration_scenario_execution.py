from integration_assertions_output import run_assertions
from integration_models import ScenarioResult
from integration_scoring import (
    calculate_experience_score,
    check_minimum_experience_score,
)
from integration_session import run_claude_session


def run_live_scenario(
    scenario, scenario_name, prompt, workspace_directory, timeout, model
):
    trace = run_claude_session(
        prompt=prompt,
        workspace_directory=workspace_directory,
        timeout_seconds=timeout,
        model=model,
    )
    if trace.exit_code == 124:
        return _failed_scenario_result(
            scenario_name,
            trace,
            workspace_directory,
            f"Session timed out after {timeout}s",
        )
    if trace.exit_code != 0:
        return _failed_scenario_result(
            scenario_name,
            trace,
            workspace_directory,
            f"Claude session exited with code {trace.exit_code}",
        )
    return _scored_scenario_result(scenario, scenario_name, trace, workspace_directory)


def _failed_scenario_result(scenario_name, trace, workspace_directory, error):
    return ScenarioResult(
        scenario_name=scenario_name,
        passed=False,
        assertion_results=[],
        trace=trace,
        workspace_directory=workspace_directory,
        duration_seconds=trace.duration_seconds,
        error=error,
    )


def _scored_scenario_result(scenario, scenario_name, trace, workspace_directory):
    assertion_results = run_assertions(
        trace,
        scenario.get("assertions", {}),
        workspace_directory=workspace_directory,
    )
    experience_score = calculate_experience_score(trace, assertion_results)
    if "minimum_experience_score" in scenario:
        assertion_results.append(
            check_minimum_experience_score(
                experience_score, scenario["minimum_experience_score"]
            )
        )
    all_passed = all(assertion_result.passed for assertion_result in assertion_results)
    return ScenarioResult(
        scenario_name=scenario_name,
        passed=all_passed,
        assertion_results=assertion_results,
        trace=trace,
        workspace_directory=workspace_directory,
        duration_seconds=trace.duration_seconds,
        experience_score=experience_score,
    )
