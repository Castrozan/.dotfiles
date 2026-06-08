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


def test_pane_indicates_stuck_modal_detects_blocking_usage_limit_prompt():
    pane_content = (
        "What do you want to do?\n"
        " ❯ Adjust monthly spend limit\n"
        "   Wait for limit to reset\n"
        "   Resets 3am (America/Sao_Paulo)\n"
    )
    assert stuck_indicators.pane_indicates_stuck_modal(pane_content) is True


def test_pane_indicates_stuck_modal_detects_weekly_limit_banner():
    pane_content = "You've hit your weekly limit · resets 3am (America/Sao_Paulo)\n"
    assert stuck_indicators.pane_indicates_stuck_modal(pane_content) is True


def test_pane_indicates_stuck_modal_detects_login_prompt():
    pane_content = (
        "Please run /login · API Error: 401 Invalid authentication credentials\n"
    )
    assert stuck_indicators.pane_indicates_stuck_modal(pane_content) is True


def test_pane_indicates_authentication_failure_detects_invalid_credentials():
    pane_content = "API Error: 401 Invalid authentication credentials\n"
    assert stuck_indicators.pane_indicates_authentication_failure(pane_content) is True


def test_pane_indicates_authentication_failure_ignores_usage_limit():
    pane_content = "You've hit your weekly limit\n"
    assert stuck_indicators.pane_indicates_authentication_failure(pane_content) is False


def test_pane_indicates_stuck_modal_ignores_idle_repl_pane():
    pane_content = (
        "● Heartbeat scheduled, nothing pending - standing by for messages.\n❯\n"
    )
    assert stuck_indicators.pane_indicates_stuck_modal(pane_content) is False


def test_watchdog_terminates_session_when_pane_shows_auth_failure(monkeypatch):
    monkeypatch.setattr(session_watchdog, "WATCHDOG_POLL_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(
        session_watchdog,
        "capture_pane_content",
        lambda _tmux_target: (
            "Please run /login · API Error: 401 Invalid authentication credentials\n"
        ),
    )
    terminated_process_ids: list[int] = []

    def terminate_and_record(root_process_id: int) -> None:
        terminated_process_ids.append(root_process_id)
        session_watchdog.os.kill(root_process_id, session_watchdog.signal.SIGKILL)

    monkeypatch.setattr(
        session_watchdog,
        "terminate_process_tree",
        terminate_and_record,
    )
    _runtime_seconds, was_stuck_kill = session_watchdog.run_launch_command_once(
        "sleep 30",
        None,
        "clawde:golden",
    )
    assert was_stuck_kill is True
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
