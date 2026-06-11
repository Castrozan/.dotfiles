import importlib.util
import json
import pathlib
import sys

import pytest

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


class _StopSupervising(Exception):
    pass


def _write_launch_config(config_path, launch_command, daily_session_rotation=False):
    config_path.write_text(
        json.dumps(
            {
                "launch_command": launch_command,
                "heartbeat_driver_argv": None,
                "active_hours_start": None,
                "active_hours_end": None,
                "daily_session_rotation": daily_session_rotation,
                "tmux_session": None,
            }
        )
    )


def test_load_agent_launch_config_reads_json(tmp_path):
    config_file = tmp_path / "agent.json"
    _write_launch_config(config_file, "claude --name steward")
    assert (
        wrapper.load_agent_launch_config(str(config_file))["launch_command"]
        == "claude --name steward"
    )


def test_supervise_rereads_config_on_each_restart(monkeypatch, tmp_path):
    config_file = tmp_path / "agent.json"
    _write_launch_config(config_file, "first")
    launch_commands_run = []

    def fake_run_launch_command_once(
        launch_command, heartbeat_driver_argv, tmux_target, **_kwargs
    ):
        launch_commands_run.append(launch_command)
        if len(launch_commands_run) == 1:
            _write_launch_config(config_file, "second")
            return (0.0, False)
        raise _StopSupervising()

    monkeypatch.setattr(
        wrapper, "run_launch_command_once", fake_run_launch_command_once
    )
    monkeypatch.setattr(wrapper, "is_within_active_hours", lambda start, end: True)
    monkeypatch.setattr(wrapper, "should_rotate_session", lambda rotation, date: False)
    monkeypatch.setattr(wrapper.time, "sleep", lambda seconds: None)

    with pytest.raises(_StopSupervising):
        wrapper.supervise_agent_forever("steward", str(config_file))

    assert launch_commands_run == ["first", "second"]


def test_session_rotation_drops_pending_resume_so_relaunch_is_fresh(
    monkeypatch, tmp_path
):
    config_file = tmp_path / "agent.json"
    _write_launch_config(config_file, "claude", daily_session_rotation=True)
    wrapper.redeploy_signal_state.resume_requested = True
    observed_resume_continue = []

    def fake_run_launch_command_once(
        launch_command, heartbeat_driver_argv, tmux_target, **kwargs
    ):
        observed_resume_continue.append(kwargs.get("resume_continue"))
        raise _StopSupervising()

    monkeypatch.setattr(
        wrapper, "run_launch_command_once", fake_run_launch_command_once
    )
    monkeypatch.setattr(wrapper, "is_within_active_hours", lambda start, end: True)
    monkeypatch.setattr(wrapper, "should_rotate_session", lambda rotation, date: True)
    monkeypatch.setattr(wrapper.time, "sleep", lambda seconds: None)

    with pytest.raises(_StopSupervising):
        wrapper.supervise_agent_forever("steward", str(config_file))

    assert observed_resume_continue == [False], (
        "a pending redeploy that lands on a session-rotation day must launch fresh, "
        "not --continue onto a day-old session that raises the resume-confirmation "
        "dialog and wedges the agent"
    )


def test_supervise_retries_when_config_unreadable(monkeypatch, tmp_path):
    recorded_sleeps = []

    def fake_sleep(seconds):
        recorded_sleeps.append(seconds)
        raise _StopSupervising()

    monkeypatch.setattr(wrapper.time, "sleep", fake_sleep)

    with pytest.raises(_StopSupervising):
        wrapper.supervise_agent_forever("steward", str(tmp_path / "missing.json"))

    assert recorded_sleeps
