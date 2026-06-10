import importlib.util
import pathlib
import signal

CLAWDE_SCRIPTS_DIRECTORY = pathlib.Path(__file__).resolve().parent.parent.parent


def _load_clawde_redeploy_module():
    module_spec = importlib.util.spec_from_file_location(
        "clawde_redeploy", CLAWDE_SCRIPTS_DIRECTORY / "clawde-redeploy.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


clawde_redeploy = _load_clawde_redeploy_module()


def test_find_agent_wrapper_process_ids_parses_pgrep_output(monkeypatch):
    class CompletedProcessStub:
        stdout = "111\n222\n333\n"

    monkeypatch.setattr(
        clawde_redeploy.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcessStub(),
    )
    assert clawde_redeploy.find_agent_wrapper_process_ids() == [111, 222, 333]


def test_describe_agent_wrappers_extracts_name_and_session(monkeypatch):
    monkeypatch.setattr(
        clawde_redeploy, "find_agent_wrapper_process_ids", lambda: [501, 502]
    )
    command_lines = {
        501: "python wrapper.py --agent-name silver --config-file /c/silver.json",
        502: "python wrapper.py --agent-name steward --config-file /c/steward.json",
    }
    monkeypatch.setattr(
        clawde_redeploy, "read_full_command_line", lambda pid: command_lines[pid]
    )
    monkeypatch.setattr(
        clawde_redeploy,
        "read_tmux_session_from_launch_config",
        lambda config_file_path: "clawde",
    )
    assert clawde_redeploy.describe_agent_wrappers() == [
        {"process_id": 501, "agent_name": "silver", "tmux_session": "clawde"},
        {"process_id": 502, "agent_name": "steward", "tmux_session": "clawde"},
    ]


def test_describe_agent_wrappers_skips_wrapper_without_config_file(monkeypatch):
    monkeypatch.setattr(
        clawde_redeploy, "find_agent_wrapper_process_ids", lambda: [601]
    )
    monkeypatch.setattr(
        clawde_redeploy,
        "read_full_command_line",
        lambda pid: "python wrapper.py --agent-name orphan",
    )
    assert clawde_redeploy.describe_agent_wrappers() == []


def test_describe_agent_wrappers_skips_wrapper_whose_config_lacks_session(monkeypatch):
    monkeypatch.setattr(
        clawde_redeploy, "find_agent_wrapper_process_ids", lambda: [701]
    )
    monkeypatch.setattr(
        clawde_redeploy,
        "read_full_command_line",
        lambda pid: "python wrapper.py --agent-name ghost --config-file /c/ghost.json",
    )
    monkeypatch.setattr(
        clawde_redeploy,
        "read_tmux_session_from_launch_config",
        lambda config_file_path: None,
    )
    assert clawde_redeploy.describe_agent_wrappers() == []


def test_signal_agent_wrappers_sends_sigusr1_to_each(monkeypatch):
    signalled_calls = []
    monkeypatch.setattr(
        clawde_redeploy.os,
        "kill",
        lambda process_id, signal_number: signalled_calls.append(
            (process_id, signal_number)
        ),
    )
    clawde_redeploy.signal_agent_wrappers_to_restart_on_continued_sessions(
        [{"process_id": 7}, {"process_id": 8}]
    )
    assert signalled_calls == [(7, signal.SIGUSR1), (8, signal.SIGUSR1)]


def test_signal_agent_wrappers_ignores_already_exited_process(monkeypatch):
    def raise_process_lookup_error(process_id, signal_number):
        raise ProcessLookupError

    monkeypatch.setattr(clawde_redeploy.os, "kill", raise_process_lookup_error)
    clawde_redeploy.signal_agent_wrappers_to_restart_on_continued_sessions(
        [{"process_id": 9}]
    )


def test_spawn_resume_nudges_builds_session_window_argv(monkeypatch):
    spawned_argvs = []
    monkeypatch.setenv(
        clawde_redeploy.RESUME_NUDGE_SCRIPT_ENVIRONMENT_VARIABLE,
        "/path/resume_nudge.py",
    )
    monkeypatch.setattr(clawde_redeploy.sys, "executable", "/python")
    monkeypatch.setattr(
        clawde_redeploy.subprocess, "Popen", lambda argv: spawned_argvs.append(argv)
    )
    clawde_redeploy.spawn_resume_nudges(
        [{"agent_name": "silver", "tmux_session": "clawde"}]
    )
    assert spawned_argvs == [
        [
            "/python",
            "/path/resume_nudge.py",
            "--session",
            "clawde",
            "--window",
            "silver",
        ]
    ]


def test_spawn_resume_nudges_noop_without_env(monkeypatch):
    spawned_argvs = []
    monkeypatch.delenv(
        clawde_redeploy.RESUME_NUDGE_SCRIPT_ENVIRONMENT_VARIABLE, raising=False
    )
    monkeypatch.setattr(
        clawde_redeploy.subprocess, "Popen", lambda argv: spawned_argvs.append(argv)
    )
    clawde_redeploy.spawn_resume_nudges(
        [{"agent_name": "silver", "tmux_session": "clawde"}]
    )
    assert spawned_argvs == []
