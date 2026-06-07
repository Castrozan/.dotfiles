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
