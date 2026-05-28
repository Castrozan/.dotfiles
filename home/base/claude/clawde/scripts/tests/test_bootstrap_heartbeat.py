import importlib.util
import pathlib
import sys


def _load_bootstrap_module():
    module_path = (
        pathlib.Path(__file__).resolve().parent.parent / "bootstrap-heartbeat.py"
    )
    module_spec = importlib.util.spec_from_file_location(
        "bootstrap_heartbeat", module_path
    )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules["bootstrap_heartbeat"] = module
    module_spec.loader.exec_module(module)
    return module


bootstrap_module = _load_bootstrap_module()


def test_bootstrap_buffer_name_is_unique_per_target():
    name_for_first_agent = bootstrap_module.build_bootstrap_buffer_name("clawde:jenny")
    name_for_second_agent = bootstrap_module.build_bootstrap_buffer_name(
        "esfinge:esfinge"
    )
    assert name_for_first_agent != name_for_second_agent, (
        "two agents bootstrapping concurrently must use distinct tmux buffer names; "
        "a shared name lets one agent's delete-buffer wipe another's before it pastes"
    )


def test_bootstrap_buffer_name_has_no_tmux_target_separator():
    buffer_name = bootstrap_module.build_bootstrap_buffer_name("esfinge:esfinge")
    assert ":" not in buffer_name, (
        "the ':' that separates session from window in a tmux target must not leak "
        "into the buffer name"
    )
