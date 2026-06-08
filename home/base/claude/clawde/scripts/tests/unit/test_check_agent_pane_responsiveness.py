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


checker = _load_agent_wrapper_module("check_agent_pane_responsiveness")

IDLE_REPL_PANE = "● standing by.\n❯\n"
AUTH_FAILURE_MODAL_PANE = (
    "Please run /login · API Error: 401 Invalid authentication credentials\n"
)
DISCUSSING_AUTH_ERROR_THEN_IDLE_PANE = (
    "The pane shows API Error: 401 / Please run /login - that is what we fix.\n❯\n"
)


def test_healthy_when_second_capture_is_idle_prompt():
    assert (
        checker.determine_pane_health_exit_code(AUTH_FAILURE_MODAL_PANE, IDLE_REPL_PANE)
        == checker.HEALTHY_EXIT_CODE
    )


def test_healthy_when_agent_merely_discusses_auth_error_at_prompt():
    assert (
        checker.determine_pane_health_exit_code(
            DISCUSSING_AUTH_ERROR_THEN_IDLE_PANE,
            DISCUSSING_AUTH_ERROR_THEN_IDLE_PANE,
        )
        == checker.HEALTHY_EXIT_CODE
    )


def test_healthy_when_pane_is_progressing_between_captures():
    assert (
        checker.determine_pane_health_exit_code(
            "Building... 12s\n", "Building... 15s\n"
        )
        == checker.HEALTHY_EXIT_CODE
    )


def test_unresponsive_when_pane_is_frozen_on_auth_modal():
    assert (
        checker.determine_pane_health_exit_code(
            AUTH_FAILURE_MODAL_PANE, AUTH_FAILURE_MODAL_PANE
        )
        == checker.UNRESPONSIVE_EXIT_CODE
    )


def test_unresponsive_when_pane_shows_usage_limit_modal():
    usage_limit_pane = "You've hit your weekly limit · resets 3am\n"
    assert (
        checker.determine_pane_health_exit_code(usage_limit_pane, usage_limit_pane)
        == checker.UNRESPONSIVE_EXIT_CODE
    )


def test_healthy_when_second_capture_fails():
    assert (
        checker.determine_pane_health_exit_code(AUTH_FAILURE_MODAL_PANE, None)
        == checker.HEALTHY_EXIT_CODE
    )
