import shutil
import tempfile
import time
from pathlib import Path

from e2e_assertions_workspace import run_e2e_assertions
from e2e_models import E2eScenarioResult, TerminalSessionTrace
from e2e_scoring import calculate_e2e_experience_score
from e2e_tmux import (
    E2E_SESSION_PREFIX,
    create_isolated_tmux_session_for_test,
    destroy_test_session,
    discover_tmux_socket_path,
    launch_claude_in_tmux_session,
)
from e2e_tmux_io import (
    capture_full_terminal_output,
    send_prompt_to_claude_session,
    wait_for_claude_input_prompt_indicator,
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

    socket_path = discover_tmux_socket_path()
    if not socket_path:
        return E2eScenarioResult(
            scenario_name=scenario_name,
            passed=False,
            assertion_results=[],
            trace=TerminalSessionTrace(),
            workspace_directory=None,
            duration_seconds=0,
            error="tmux socket not found",
        )

    sanitized = sanitize_name_for_session(scenario_name)
    timestamp = int(time.time())
    session_name = f"{E2E_SESSION_PREFIX}{sanitized}-{timestamp}"
    E2E_WORKSPACE_PARENT.mkdir(parents=True, exist_ok=True)
    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"e2e-{sanitized}-",
            dir=E2E_WORKSPACE_PARENT,
        )
    )
    timeout = scenario.get("timeout", 300)

    try:
        setup_e2e_scenario_workspace(scenario, workspace, claude_ab_mode)

        tmux_target = create_isolated_tmux_session_for_test(
            socket_path, session_name, workspace
        )

        launch_claude_in_tmux_session(socket_path, tmux_target, model)

        if not wait_for_claude_input_prompt_indicator(
            socket_path, tmux_target, max_attempts=45
        ):
            return E2eScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=TerminalSessionTrace(),
                workspace_directory=workspace,
                duration_seconds=0,
                error="Claude failed to start (no prompt detected)",
            )

        prompts = scenario.get("prompts", [])
        if not prompts:
            single_prompt = scenario.get("prompt", "")
            if single_prompt:
                prompts = [single_prompt]

        start_time = time.time()

        for prompt_text in prompts:
            send_prompt_to_claude_session(socket_path, tmux_target, prompt_text)
            completed = wait_for_response_completion(
                socket_path,
                tmux_target,
                prompt_text=prompt_text,
                timeout_seconds=timeout,
            )
            if not completed:
                raw_output = capture_full_terminal_output(socket_path, tmux_target)
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
                    error=f"Timed out after {timeout}s",
                )

        raw_output = capture_full_terminal_output(socket_path, tmux_target)
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
        destroy_test_session(socket_path, session_name)
        shutil.rmtree(workspace, ignore_errors=True)
