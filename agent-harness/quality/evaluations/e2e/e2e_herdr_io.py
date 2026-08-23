import time

from e2e_harness_profiles import HarnessProfile
from e2e_herdr import herdr_result_payload, run_herdr_command

INPUT_SETTLE_SECONDS = 2
TYPED_INPUT_SETTLE_SECONDS = 0.25
COMPACTION_ENTRY_POINT_SETTLE_SECONDS = 2.0
FULL_SCROLLBACK_LINE_BUDGET = 5000
RESPONSE_POLL_INTERVAL_SECONDS = 1.0
RESPONSE_QUIESCENCE_SAMPLES = 4
STARTUP_SETTLE_TIMEOUT_SECONDS = 180


def wait_for_agent_status(
    pane_id: str, agent_status: str, timeout_seconds: float
) -> bool:
    completed = run_herdr_command(
        [
            "wait",
            "agent-status",
            pane_id,
            "--status",
            agent_status,
            "--timeout",
            str(int(timeout_seconds * 1000)),
        ],
        timeout_seconds=timeout_seconds + 10,
    )
    return completed.returncode == 0


def pane_hosts_a_live_agent(pane_id: str) -> bool:
    payload = herdr_result_payload(run_herdr_command(["agent", "get", pane_id]))
    return bool(payload.get("agent", {}).get("agent"))


def wait_for_agent_to_become_ready(
    pane_id: str, profile: HarnessProfile, timeout_seconds: float = 90
) -> bool:
    if not wait_for_agent_status(pane_id, "idle", timeout_seconds):
        return False
    if not wait_for_startup_output_to_settle(pane_id, profile.busy_marker):
        return False
    time.sleep(INPUT_SETTLE_SECONDS)
    return True


def send_prompt_to_agent_session(pane_id: str, prompt_text: str) -> bool:
    collapsed_prompt = " ".join(prompt_text.strip().split())
    typed = run_herdr_command(["pane", "send-text", pane_id, collapsed_prompt])
    if typed.returncode != 0:
        return False
    time.sleep(TYPED_INPUT_SETTLE_SECONDS)
    return run_herdr_command(["pane", "send-keys", pane_id, "Enter"]).returncode == 0


def wait_for_pane_quiescence(
    pane_id: str,
    initial_output: str,
    timeout_seconds: float,
    require_change: bool,
    busy_marker: str = "",
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    previous_output = initial_output
    unchanged_samples = 0
    the_pane_ever_changed = False
    while time.monotonic() < deadline:
        time.sleep(RESPONSE_POLL_INTERVAL_SECONDS)
        current_output = capture_visible_screen(pane_id)
        if busy_marker and busy_marker in current_output:
            the_pane_ever_changed = True
            unchanged_samples = 0
            previous_output = current_output
            continue
        if current_output != previous_output:
            the_pane_ever_changed = True
            unchanged_samples = 0
            previous_output = current_output
            continue
        unchanged_samples += 1
        if unchanged_samples < RESPONSE_QUIESCENCE_SAMPLES:
            continue
        if the_pane_ever_changed or not require_change:
            return True
    return False


def wait_for_response_completion(
    pane_id: str,
    output_after_send: str,
    timeout_seconds: float = 300,
    busy_marker: str = "",
) -> bool:
    return wait_for_pane_quiescence(
        pane_id,
        output_after_send,
        timeout_seconds,
        require_change=True,
        busy_marker=busy_marker,
    )


def wait_for_startup_output_to_settle(
    pane_id: str,
    busy_marker: str = "",
    timeout_seconds: float = STARTUP_SETTLE_TIMEOUT_SECONDS,
) -> bool:
    return wait_for_pane_quiescence(
        pane_id,
        capture_visible_screen(pane_id),
        timeout_seconds,
        require_change=False,
        busy_marker=busy_marker,
    )


def read_pane(pane_id: str, source: str) -> str:
    completed = run_herdr_command(
        [
            "pane",
            "read",
            pane_id,
            "--source",
            source,
            "--lines",
            str(FULL_SCROLLBACK_LINE_BUDGET),
        ],
        timeout_seconds=30,
    )
    return completed.stdout


def capture_full_terminal_output(pane_id: str) -> str:
    return read_pane(pane_id, "recent-unwrapped")


def capture_visible_screen(pane_id: str) -> str:
    return read_pane(pane_id, "visible")


def capture_screen_and_scrollback(pane_id: str) -> str:
    return capture_visible_screen(pane_id) + capture_full_terminal_output(pane_id)


def open_compaction_entry_point(pane_id: str, profile: HarnessProfile) -> bool:
    for key in profile.compaction_prelude_keys:
        if run_herdr_command(["pane", "send-keys", pane_id, key]).returncode != 0:
            return False
        time.sleep(COMPACTION_ENTRY_POINT_SETTLE_SECONDS)
    return True


def compact_agent_session(
    pane_id: str, profile: HarnessProfile, timeout_seconds: float = 300
) -> bool:
    output_before_compaction = capture_visible_screen(pane_id)
    if not open_compaction_entry_point(pane_id, profile):
        return False
    if not send_prompt_to_agent_session(pane_id, profile.compaction_directive):
        return False
    if not wait_for_response_completion(
        pane_id,
        output_before_compaction,
        timeout_seconds=timeout_seconds,
        busy_marker=profile.busy_marker,
    ):
        return False
    output_after_compaction = capture_screen_and_scrollback(pane_id)
    if (
        profile.compaction_refusal_marker
        and profile.compaction_refusal_marker in output_after_compaction
    ):
        return False
    return profile.compaction_confirmation_marker in output_after_compaction
