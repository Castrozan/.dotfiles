import importlib.util
import pathlib
import sys

AGENT_WRAPPER_DIRECTORY = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "agent-wrapper"
)


def _load_agent_wrapper_module(module_name: str):
    if str(AGENT_WRAPPER_DIRECTORY) not in sys.path:
        sys.path.insert(0, str(AGENT_WRAPPER_DIRECTORY))
    module_path = AGENT_WRAPPER_DIRECTORY / f"{module_name}.py"
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    module_spec.loader.exec_module(module)
    return module


stuck_indicators = _load_agent_wrapper_module("stuck_indicators")
session_watchdog = _load_agent_wrapper_module("session_watchdog")

IDLE_REPL_PANE = "● Heartbeat scheduled, nothing pending - standing by.\n❯\n"
AUTH_FAILURE_MODAL_PANE = (
    "Please run /login · API Error: 401 Invalid authentication credentials\n"
)
USAGE_LIMIT_MODAL_PANE = (
    "What do you want to do?\n"
    " ❯ Adjust monthly spend limit\n"
    "   Wait for limit to reset\n"
)
AGENT_DISCUSSING_AUTH_ERROR_THEN_IDLE_PANE = (
    "I see the steward pane shows API Error: 401 / Please run /login - that is the\n"
    "auth-stuck state we are fixing.\n❯\n"
)


def test_pane_is_at_idle_repl_prompt_true_for_idle_pane():
    assert stuck_indicators.pane_is_at_idle_repl_prompt(IDLE_REPL_PANE) is True


def test_pane_is_at_idle_repl_prompt_false_for_frozen_modal():
    assert (
        stuck_indicators.pane_is_at_idle_repl_prompt(AUTH_FAILURE_MODAL_PANE) is False
    )


def test_pane_is_at_idle_repl_prompt_false_at_onboarding_even_with_prompt_glyph():
    onboarding_pane = "Select login method\n ❯ Claude account with subscription\n"
    assert stuck_indicators.pane_is_at_idle_repl_prompt(onboarding_pane) is False


def test_idle_repl_pane_is_never_stuck_evidence_even_when_frozen():
    assert (
        stuck_indicators.pane_poll_is_stuck_evidence(IDLE_REPL_PANE, IDLE_REPL_PANE)
        is False
    )


def test_agent_discussing_auth_error_but_back_at_prompt_is_not_stuck():
    assert (
        stuck_indicators.pane_poll_is_stuck_evidence(
            AGENT_DISCUSSING_AUTH_ERROR_THEN_IDLE_PANE,
            AGENT_DISCUSSING_AUTH_ERROR_THEN_IDLE_PANE,
        )
        is False
    )


def test_progressing_pane_is_not_stuck_even_without_prompt():
    assert (
        stuck_indicators.pane_poll_is_stuck_evidence(
            "Running step 2 of 5... 41s\n", "Running step 2 of 5... 12s\n"
        )
        is False
    )


def test_frozen_non_idle_pane_is_stuck_evidence():
    assert (
        stuck_indicators.pane_poll_is_stuck_evidence(
            AUTH_FAILURE_MODAL_PANE, AUTH_FAILURE_MODAL_PANE
        )
        is True
    )


def test_first_poll_without_previous_capture_is_not_stuck_evidence():
    assert (
        stuck_indicators.pane_poll_is_stuck_evidence(AUTH_FAILURE_MODAL_PANE, None)
        is False
    )


def test_usage_limit_modal_is_stuck_evidence_on_first_sight():
    assert (
        stuck_indicators.pane_poll_is_stuck_evidence(USAGE_LIMIT_MODAL_PANE, None)
        is True
    )


def test_watchdog_terminates_session_when_pane_is_frozen_and_not_idle(monkeypatch):
    monkeypatch.setattr(session_watchdog, "WATCHDOG_POLL_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(
        session_watchdog,
        "capture_pane_content",
        lambda _tmux_target: AUTH_FAILURE_MODAL_PANE,
    )
    terminated_process_ids: list[int] = []

    def terminate_and_record(root_process_id: int) -> None:
        terminated_process_ids.append(root_process_id)
        session_watchdog.os.kill(root_process_id, session_watchdog.signal.SIGKILL)

    monkeypatch.setattr(
        session_watchdog, "terminate_process_tree", terminate_and_record
    )
    _runtime_seconds, was_stuck_kill = session_watchdog.run_launch_command_once(
        "sleep 30",
        None,
        "clawde:golden",
    )
    assert was_stuck_kill is True
    assert len(terminated_process_ids) == 1


def test_watchdog_terminates_when_heartbeat_driver_gives_up_on_repl(monkeypatch):
    monkeypatch.setattr(session_watchdog, "WATCHDOG_POLL_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(
        session_watchdog, "capture_pane_content", lambda _tmux_target: None
    )
    terminated_process_ids: list[int] = []

    def terminate_and_record(root_process_id: int) -> None:
        terminated_process_ids.append(root_process_id)
        session_watchdog.os.kill(root_process_id, session_watchdog.signal.SIGKILL)

    monkeypatch.setattr(
        session_watchdog, "terminate_process_tree", terminate_and_record
    )
    _runtime_seconds, was_stuck_kill = session_watchdog.run_launch_command_once(
        "sleep 30",
        ["bash", "-c", "exit 1"],
        "clawde:steward",
    )
    assert was_stuck_kill is True, (
        "when the heartbeat driver exits because it never found a live REPL, the "
        "session is wedged at a pre-prompt modal (e.g. the resume-confirmation "
        "dialog) and the watchdog must terminate it to force a fresh restart"
    )
    assert len(terminated_process_ids) == 1


def test_resume_continue_exposes_continue_flag_to_launch_command(tmp_path):
    captured_flag = tmp_path / "flag.txt"
    session_watchdog.run_launch_command_once(
        f'printf "%s" "$CLAWDE_RESUME_FLAG" > "{captured_flag}"',
        None,
        None,
        resume_continue=True,
    )
    assert captured_flag.read_text() == "--continue"


def test_default_launch_leaves_resume_flag_empty(tmp_path):
    captured_flag = tmp_path / "flag.txt"
    session_watchdog.run_launch_command_once(
        f'printf "%s" "$CLAWDE_RESUME_FLAG" > "{captured_flag}"',
        None,
        None,
    )
    assert captured_flag.read_text() == ""


def test_register_child_pid_callback_receives_live_then_none(tmp_path):
    observed_process_ids = []
    session_watchdog.run_launch_command_once(
        "true",
        None,
        None,
        register_child_pid=observed_process_ids.append,
    )
    assert len(observed_process_ids) == 2
    assert isinstance(observed_process_ids[0], int)
    assert observed_process_ids[1] is None
