import importlib.util
import pathlib
import sys

AGENT_WRAPPER_DIRECTORY = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "agent-wrapper"
)
sys.path.insert(0, str(AGENT_WRAPPER_DIRECTORY))


def _load_wrapper_module():
    module_spec = importlib.util.spec_from_file_location(
        "wrapper", AGENT_WRAPPER_DIRECTORY / "wrapper.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


wrapper = _load_wrapper_module()


def test_redeploy_request_sets_resume_flag_without_a_child():
    wrapper.redeploy_signal_state.resume_requested = False
    wrapper.redeploy_signal_state.current_child_process_id = None
    wrapper.request_resume_restart_now()
    assert wrapper.redeploy_signal_state.resume_requested is True


def test_register_current_child_process_id_updates_state():
    wrapper.register_current_child_process_id(4242)
    assert wrapper.redeploy_signal_state.current_child_process_id == 4242
    wrapper.register_current_child_process_id(None)
    assert wrapper.redeploy_signal_state.current_child_process_id is None
