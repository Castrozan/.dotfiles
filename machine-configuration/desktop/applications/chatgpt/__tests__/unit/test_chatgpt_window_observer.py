import json
import socket
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import MagicMock, Mock

import pytest

import chatgpt_window_observer as window_observer
from chatgpt_window_observer import ChatGPTWindowObserver


@pytest.fixture
def observer(monkeypatch):
    with TemporaryDirectory(prefix="chatgpt-desktop-", dir="/tmp") as runtime_directory:
        directory = Path(runtime_directory) / "hypr" / "test-session"
        directory.mkdir(parents=True)
        monkeypatch.setenv("XDG_RUNTIME_DIR", runtime_directory)
        monkeypatch.setenv("HYPRLAND_INSTANCE_SIGNATURE", "test-session")
        observed = ChatGPTWindowObserver()
        yield observed
        observed.disconnect()


def reply_once(server, response):
    with server.accept()[0] as connection:
        connection.settimeout(2)
        assert connection.recv(32) == b"j/clients"
        connection.sendall(response)


def test_real_desktop_socket_reports_owned_window(observer):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as events:
        events.bind(str(observer.socket_directory / ".socket2.sock"))
        events.listen()
        events.settimeout(2)
        observer.poll(0)
        event_connection = events.accept()[0]
        with (
            event_connection,
            socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as control,
        ):
            control.bind(str(observer.socket_directory / ".socket.sock"))
            control.listen()
            control.settimeout(2)
            response = json.dumps(
                [{"pid": 42, "address": "0xabc", "mapped": True}]
            ).encode()
            reply = Thread(target=reply_once, args=(control, response))
            reply.start()
            observer.refresh({42})
            reply.join(2)
            assert not reply.is_alive()
            assert observer.window_open is True
    observer.disconnect()


def test_focus_events_do_not_change_mode_and_close_events_request_refresh(observer):
    reader, writer = socket.socketpair()
    observer.event_socket = reader
    observer.refresh_needed = False
    observer.window_open = True
    with writer:
        writer.sendall(b"activewindow>>foreign\nclosewin")
        observer.poll(0.1)
        assert observer.refresh_needed is False
        assert observer.window_open is True
        writer.sendall(b"dow>>abc\n")
        observer.poll(0.1)
        assert observer.refresh_needed is True
    observer.poll(0.1)
    assert observer.window_open is None


@pytest.mark.parametrize("failure", [ConnectionResetError(), b"x" * 65536])
def test_event_failure_retains_unknown_state_and_closes_connection(
    observer, monkeypatch, failure
):
    connection = Mock()
    observer.event_socket = connection
    observer.window_open = False
    observer.pending_events = b"x" * 70000
    connection.recv.side_effect = [failure]
    monkeypatch.setattr(
        window_observer.select, "select", lambda *args: ([connection], [], [])
    )
    observer.poll(0)
    assert observer.window_open is None
    assert observer.event_socket is None
    connection.close.assert_called_once_with()


def test_missing_desktop_retries_after_backoff(observer, monkeypatch):
    monkeypatch.setattr(window_observer.time, "monotonic", lambda: 10)
    observer.poll(0)
    assert observer.window_open is None
    assert observer.next_connection_attempt == 15
    connect = Mock()
    monkeypatch.setattr(observer, "connect", connect)
    observer.poll(0)
    connect.assert_not_called()


def test_absent_desktop_environment_cannot_select_background(monkeypatch):
    monkeypatch.delenv("HYPRLAND_INSTANCE_SIGNATURE", raising=False)
    observer = ChatGPTWindowObserver()
    observer.poll(0)
    observer.refresh({42})
    assert observer.window_open is None


@pytest.mark.parametrize("chunks", [[b"{invalid", b""], [b"x" * 65536] * 33])
def test_invalid_or_oversized_desktop_response_is_unknown(
    observer, monkeypatch, chunks
):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.recv.side_effect = chunks
    monkeypatch.setattr(window_observer.socket, "socket", lambda *args: connection)
    event_connection = Mock()
    observer.event_socket = event_connection
    observer.window_open = False
    observer.refresh({42})
    assert observer.window_open is None
    event_connection.close.assert_called_once_with()
