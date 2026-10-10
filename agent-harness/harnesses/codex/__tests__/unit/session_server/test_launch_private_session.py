from pathlib import Path
import signal
import subprocess
from unittest.mock import Mock

import pytest

import launch_private_session as launcher


@pytest.fixture
def private_launch(monkeypatch):
    monkeypatch.setenv("CODEX_LAUNCHER_BINARY", "/codex")
    monkeypatch.setenv("CODEX_THREAD_ID", "inherited-parent")
    monkeypatch.setenv("HERDR_PANE_ID", "own-pane")
    server = Mock(pid=456)
    server.poll.return_value = None
    client = Mock()
    client.wait.return_value = 7
    client.poll.return_value = 7
    processes = Mock(side_effect=[server, client])
    monkeypatch.setattr(launcher.subprocess, "Popen", processes)
    monkeypatch.setattr(launcher.threading, "Thread", Mock())
    ready = Mock()
    monkeypatch.setattr(launcher, "wait_for_session_server", ready)
    kill_group = Mock()
    monkeypatch.setattr(launcher.os, "killpg", kill_group)
    monkeypatch.setattr(launcher, "process_group_exists", lambda identifier: False)
    return server, client, processes, ready, kill_group


def test_private_launch_keeps_client_arguments_and_owns_server_lifetime(private_launch):
    server, client, processes, _, kill_group = private_launch
    arguments = ["--sandbox", "danger-full-access", "resume", "--last"]
    assert launcher.run_private_session(arguments) == 7
    server_call, client_call = processes.call_args_list
    endpoint = server_call.args[0][-1]
    assert server_call.args[0] == ["/codex", "app-server", "--listen", endpoint]
    assert client_call.args[0] == ["/codex", "--remote", endpoint, *arguments]
    assert "start_new_session" not in client_call.kwargs
    environment = server_call.kwargs["env"]
    assert environment["HERDR_PANE_ID"] == "own-pane"
    assert "CODEX_THREAD_ID" not in environment
    socket_path = environment["CODEX_SESSION_SOCKET_PATH"]
    assert socket_path.startswith("/tmp/codex-session-")
    assert client_call.kwargs["env"] == environment
    assert not Path(socket_path).parent.exists()
    kill_group.assert_called_once_with(server.pid, signal.SIGTERM)
    client.terminate.assert_not_called()


def test_failed_startup_never_opens_client_and_reaps_server(private_launch):
    server, _, processes, ready, kill_group = private_launch
    ready.side_effect = TimeoutError("not ready")
    with pytest.raises(TimeoutError, match="not ready"):
        launcher.run_private_session([])
    assert processes.call_count == 1
    kill_group.assert_called_once_with(server.pid, signal.SIGTERM)
    server.wait.assert_called_once_with(timeout=1.0)


def test_managed_permissions_apply_on_server_without_remote_resume_overrides(
    private_launch,
):
    _, _, processes, _, _ = private_launch
    launcher.run_private_session(
        [
            "--sandbox",
            "danger-full-access",
            "--ask-for-approval",
            "never",
            "resume",
            "thread-123",
        ]
    )
    server_call, client_call = processes.call_args_list
    assert server_call.args[0][1:5] == [
        "-c",
        'sandbox_mode="danger-full-access"',
        "-c",
        'approval_policy="never"',
    ]
    assert client_call.args[0][3:] == ["resume", "thread-123"]


def test_relative_codex_home_keeps_caller_location_when_server_changes_directory(
    private_launch, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CODEX_HOME", "agent-home")
    _, _, processes, _, _ = private_launch
    launcher.run_private_session(["-C", str(tmp_path / "project")])
    server_call, client_call = processes.call_args_list
    assert server_call.kwargs["cwd"] == tmp_path / "project"
    expected_home = str(tmp_path / "agent-home")
    assert server_call.kwargs["env"]["CODEX_HOME"] == expected_home
    assert client_call.kwargs["env"]["CODEX_HOME"] == expected_home


def test_signal_exit_status_retains_native_signal(private_launch):
    _, client, _, _, _ = private_launch
    client.wait.return_value = -signal.SIGTERM
    assert launcher.run_private_session([]) == 143


def test_stuck_server_gets_bounded_shutdown_then_group_kill(monkeypatch):
    process = Mock(pid=789)
    process.wait.side_effect = [subprocess.TimeoutExpired("codex", 1), 0]
    kill_group = Mock()
    monkeypatch.setattr(launcher.os, "killpg", kill_group)
    monkeypatch.setattr(launcher, "process_group_exists", lambda identifier: False)
    launcher.stop_process(process, process_group=True)
    assert [call.args for call in kill_group.call_args_list] == [
        (789, signal.SIGTERM),
        (789, signal.SIGKILL),
    ]


def test_cleanup_kills_remaining_children_after_server_has_exited(monkeypatch):
    server = Mock(pid=789)
    server.wait.return_value = 0
    kill_group = Mock()
    monkeypatch.setattr(launcher.os, "killpg", kill_group)
    monkeypatch.setattr(launcher, "process_group_exists", lambda identifier: True)
    monkeypatch.setattr(launcher.time, "monotonic", Mock(side_effect=[0, 0, 2]))
    monkeypatch.setattr(launcher.time, "sleep", Mock())
    launcher.stop_process(server, process_group=True)
    assert [call.args for call in kill_group.call_args_list] == [
        (789, signal.SIGTERM),
        (789, signal.SIGKILL),
    ]


def test_server_failure_terminates_attached_client():
    server, client = Mock(), Mock()
    client.poll.return_value = None
    launcher.stop_client_when_server_exits(server, client)
    server.wait.assert_called_once_with()
    client.terminate.assert_called_once_with()


def test_readiness_rejects_a_dead_server(tmp_path):
    server = Mock()
    server.poll.return_value = 1
    with pytest.raises(RuntimeError, match="exited during startup"):
        launcher.wait_for_session_server(server, tmp_path / "server.sock")


def test_readiness_is_bounded_when_socket_never_appears(tmp_path, monkeypatch):
    server = Mock()
    server.poll.return_value = None
    monkeypatch.setattr(launcher.time, "monotonic", Mock(side_effect=[0, 0, 6]))
    monkeypatch.setattr(launcher.time, "sleep", Mock())
    with pytest.raises(TimeoutError, match="within 5s"):
        launcher.wait_for_session_server(server, tmp_path / "server.sock")


def test_launcher_keeps_ctrl_c_for_terminal_client_and_restores_handlers(monkeypatch):
    handlers = {}
    monkeypatch.setattr(launcher.signal, "getsignal", lambda number: "previous")
    monkeypatch.setattr(
        launcher.signal,
        "signal",
        lambda number, handler: handlers.update({number: handler}),
    )

    def run(arguments):
        assert handlers[signal.SIGINT] is launcher.keep_interrupt_with_terminal_client
        assert handlers[signal.SIGINT](signal.SIGINT, None) is None
        with pytest.raises(SystemExit) as stopped:
            handlers[signal.SIGTERM](signal.SIGTERM, None)
        assert stopped.value.code == 143
        return 0

    monkeypatch.setattr(launcher, "run_private_session", run)
    assert launcher.main() == 0
    assert set(handlers.values()) == {"previous"}
