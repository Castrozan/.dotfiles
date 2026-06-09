import importlib.util
import pathlib
import sys

AGENT_WRAPPER_DIRECTORY = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "agent-wrapper"
)
sys.path.insert(0, str(AGENT_WRAPPER_DIRECTORY))


def _load_redeploy_signals_module():
    module_spec = importlib.util.spec_from_file_location(
        "redeploy_signals", AGENT_WRAPPER_DIRECTORY / "redeploy_signals.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


redeploy_signals = _load_redeploy_signals_module()


def test_redeploy_request_sets_resume_flag_without_a_child():
    redeploy_signals.redeploy_signal_state.resume_requested = False
    redeploy_signals.redeploy_signal_state.current_child_process_id = None
    redeploy_signals.request_resume_restart_now()
    assert redeploy_signals.redeploy_signal_state.resume_requested is True


def test_register_current_child_process_id_updates_state():
    redeploy_signals.register_current_child_process_id(4242)
    assert redeploy_signals.redeploy_signal_state.current_child_process_id == 4242
    redeploy_signals.register_current_child_process_id(None)
    assert redeploy_signals.redeploy_signal_state.current_child_process_id is None
