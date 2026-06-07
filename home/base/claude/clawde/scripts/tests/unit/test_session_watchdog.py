import importlib.util
import pathlib
import sys


def _load_session_watchdog_module():
    module_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "agent-wrapper"
        / "session_watchdog.py"
    )
    module_spec = importlib.util.spec_from_file_location(
        "session_watchdog", module_path
    )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules["session_watchdog"] = module
    module_spec.loader.exec_module(module)
    return module


session_watchdog = _load_session_watchdog_module()


def test_pane_indicates_usage_limit_modal_detects_blocking_limit_prompt():
    pane_content = (
        "What do you want to do?\n"
        " ❯ Adjust monthly spend limit\n"
        "   Wait for limit to reset\n"
        "   Resets 3am (America/Sao_Paulo)\n"
    )
    assert session_watchdog.pane_indicates_usage_limit_modal(pane_content) is True


def test_pane_indicates_usage_limit_modal_detects_weekly_limit_banner():
    pane_content = "You've hit your weekly limit · resets 3am (America/Sao_Paulo)\n"
    assert session_watchdog.pane_indicates_usage_limit_modal(pane_content) is True


def test_pane_indicates_usage_limit_modal_ignores_idle_repl_pane():
    pane_content = (
        "● Heartbeat scheduled, nothing pending - standing by for messages.\n❯\n"
    )
    assert session_watchdog.pane_indicates_usage_limit_modal(pane_content) is False


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
