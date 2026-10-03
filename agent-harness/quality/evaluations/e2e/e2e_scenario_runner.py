import shutil
import tempfile
import time
from pathlib import Path

from e2e.sessions.e2e_harness_profiles import scenario_harness_profile
from e2e.sessions.e2e_models import E2eScenarioResult, TerminalSessionTrace
from e2e.sessions.e2e_herdr import (
    E2E_TAB_LABEL_PREFIX,
    create_isolated_herdr_tab_for_test,
    destroy_test_tab,
    herdr_server_is_reachable,
    launch_agent_in_herdr_pane,
)
from e2e.sessions.e2e_herdr_io import (
    wait_for_agent_to_become_ready,
)
from e2e.sessions.e2e_scenario_results import (
    failed_e2e_scenario_result,
    successful_e2e_scenario_result,
)
from e2e.sessions.e2e_scenario_steps import run_scenario_step, scenario_steps
from e2e.sessions.e2e_workspace import (
    E2E_WORKSPACE_PARENT,
    load_scenario,
    sanitize_name_for_session,
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
        return _empty_e2e_result(scenario_name)
    return _run_live_scenario(
        scenario,
        scenario_name,
        profile,
        model,
        debug_capture,
        instruction_placement_mode,
    )


def _run_live_scenario(
    scenario, scenario_name, profile, model, debug_capture, instruction_placement_mode
):
    if not herdr_server_is_reachable():
        return _empty_e2e_result(scenario_name, "herdr server not reachable")

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
            return _empty_e2e_result(
                scenario_name, "herdr tab could not be created", workspace
            )
        pane_id = tab_handle["pane_id"]

        launch_agent_in_herdr_pane(
            pane_id, profile, scenario.get("model", model), workspace
        )

        if not wait_for_agent_to_become_ready(pane_id, profile):
            return _empty_e2e_result(
                scenario_name,
                f"{profile.name} never became ready to accept a prompt",
                workspace,
            )

        start_time = time.time()

        return _run_e2e_session(
            scenario,
            scenario_name,
            pane_id,
            profile,
            workspace,
            start_time,
            timeout,
            debug_capture,
        )
    finally:
        if tab_handle:
            destroy_test_tab(tab_handle["tab_id"])
        shutil.rmtree(workspace, ignore_errors=True)


def _run_e2e_session(
    scenario,
    scenario_name,
    pane_id,
    profile,
    workspace,
    start_time,
    timeout,
    debug_capture,
):
    for scenario_step in scenario_steps(scenario):
        failure_reason = run_scenario_step(pane_id, scenario_step, profile, timeout)
        if failure_reason:
            return failed_e2e_scenario_result(
                scenario,
                scenario_name,
                pane_id,
                workspace,
                start_time,
                failure_reason=failure_reason,
                debug_capture=debug_capture,
            )
    return successful_e2e_scenario_result(
        scenario,
        scenario_name,
        pane_id,
        workspace,
        start_time,
        debug_capture=debug_capture,
    )


def _empty_e2e_result(scenario_name, error=None, workspace=None):
    return E2eScenarioResult(
        scenario_name=scenario_name,
        passed=error is None,
        assertion_results=[],
        trace=TerminalSessionTrace(),
        workspace_directory=workspace,
        duration_seconds=0,
        error=error,
    )
