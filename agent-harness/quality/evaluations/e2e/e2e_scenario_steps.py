from e2e_herdr_io import (
    capture_full_terminal_output,
    compact_claude_session,
    send_prompt_to_claude_session,
    wait_for_response_completion,
)

COMPACTION_STEP_KEY = "compact"


def scenario_steps(scenario: dict) -> list:
    declared_steps = scenario.get("prompts", [])
    if declared_steps:
        return declared_steps
    single_prompt = scenario.get("prompt", "")
    return [single_prompt] if single_prompt else []


def step_requests_compaction(scenario_step) -> bool:
    return isinstance(scenario_step, dict) and bool(
        scenario_step.get(COMPACTION_STEP_KEY)
    )


def run_scenario_step(pane_id: str, scenario_step, timeout_seconds: float):
    if step_requests_compaction(scenario_step):
        if compact_claude_session(pane_id, timeout_seconds=timeout_seconds):
            return None
        return "session compaction was refused or never confirmed"
    if not send_prompt_to_claude_session(pane_id, scenario_step):
        return "prompt could not be delivered to the herdr pane"
    if wait_for_response_completion(
        pane_id,
        capture_full_terminal_output(pane_id),
        timeout_seconds=timeout_seconds,
    ):
        return None
    return f"Timed out after {timeout_seconds}s"
