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


checker = _load_agent_wrapper_module("check_agent_pane_for_stuck_modal")


def test_healthy_exit_code_when_pane_is_idle():
    pane_content = "● Heartbeat scheduled, nothing pending - standing by.\n❯\n"
    assert (
        checker.determine_pane_health_exit_code(pane_content)
        == checker.HEALTHY_EXIT_CODE
    )


def test_stuck_modal_exit_code_when_pane_shows_auth_failure():
    pane_content = (
        "Please run /login · API Error: 401 Invalid authentication credentials\n"
    )
    assert (
        checker.determine_pane_health_exit_code(pane_content)
        == checker.STUCK_MODAL_EXIT_CODE
    )


def test_stuck_modal_exit_code_when_pane_shows_usage_limit():
    pane_content = "You've hit your weekly limit · resets 3am\n"
    assert (
        checker.determine_pane_health_exit_code(pane_content)
        == checker.STUCK_MODAL_EXIT_CODE
    )


def test_healthy_exit_code_when_pane_capture_fails():
    assert checker.determine_pane_health_exit_code(None) == checker.HEALTHY_EXIT_CODE
