import json
import socket

import pytest

from ambient_canvas_mpv_visibility import (
    VisibilityGatedPlaybackController,
    pin_player_window_to_workspace,
    resolve_active_workspace_id,
    window_is_mapped,
)
from mpv_ambient_canvas_ipc import MpvIpcClient


def test_resolve_active_workspace_id_parses_the_focused_workspace(monkeypatch):
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed", (), {"stdout": json.dumps({"id": 11}), "returncode": 0}
        )(),
    )
    assert resolve_active_workspace_id() == 11


def test_resolve_active_workspace_id_returns_none_when_hyprctl_fails(monkeypatch):
    def fail(*args, **kwargs):
        raise FileNotFoundError("hyprctl")

    monkeypatch.setattr("ambient_canvas_mpv_visibility.subprocess.run", fail)
    assert resolve_active_workspace_id() is None


def test_window_is_mapped_finds_the_player_window(monkeypatch):
    clients = [
        {"title": "bash", "mapped": True},
        {"title": "ambient-canvas-gpu-screensaver", "mapped": True},
    ]
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed", (), {"stdout": json.dumps(clients), "returncode": 0}
        )(),
    )
    assert window_is_mapped() is True


def test_window_is_mapped_rejects_unmapped_windows(monkeypatch):
    clients = [{"title": "ambient-canvas-gpu-screensaver", "mapped": False}]
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed", (), {"stdout": json.dumps(clients), "returncode": 0}
        )(),
    )
    assert window_is_mapped() is False


def test_pin_player_window_focuses_then_fullscreens(monkeypatch):
    dispatched = []
    monkeypatch.setattr("ambient_canvas_mpv_visibility.window_is_mapped", lambda: True)
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.window_is_fullscreen", lambda: True
    )
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.run_hyprctl_command",
        lambda arguments: dispatched.append(arguments),
    )
    pin_player_window_to_workspace()
    assert dispatched == [
        ["focuswindow", "title:^ambient-canvas-gpu-screensaver$"],
        ["fullscreen"],
    ]


def test_pin_player_window_retries_until_fullscreen(monkeypatch):
    dispatched = []
    fullscreen_counts = iter([False, False, True])
    monkeypatch.setattr("ambient_canvas_mpv_visibility.window_is_mapped", lambda: True)
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.window_is_fullscreen",
        lambda: next(fullscreen_counts),
    )
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.run_hyprctl_command",
        lambda arguments: dispatched.append(arguments),
    )
    pin_player_window_to_workspace()
    assert dispatched.count(["fullscreen"]) == 3


def test_visibility_controller_pauses_when_target_workspace_is_not_active(monkeypatch):
    sent_commands = []

    class RecordingClient:
        def send_command(self, command):
            sent_commands.append(command)

    controller = VisibilityGatedPlaybackController(RecordingClient(), 11)
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.resolve_active_workspace_id", lambda: 5
    )
    controller._synchronize_with_active_workspace()
    assert sent_commands == [["set_property", "pause", "yes"]]


def test_visibility_controller_resumes_when_target_workspace_is_active(monkeypatch):
    sent_commands = []

    class RecordingClient:
        def send_command(self, command):
            sent_commands.append(command)

    controller = VisibilityGatedPlaybackController(RecordingClient(), 11)
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.resolve_active_workspace_id", lambda: 11
    )
    controller._synchronize_with_active_workspace()
    assert sent_commands == [["set_property", "pause", "no"]]


def test_mpv_client_reads_newline_delimited_json_events(tmp_path):
    socket_path = str(tmp_path / "mpv.sock")

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(socket_path)
    listener.listen(1)

    client = MpvIpcClient(socket_path).connect()

    peer, _ = listener.accept()
    peer.sendall((json.dumps({"event": "end-file", "reason": "eof"}) + "\n").encode())
    event = client.read_event()
    assert event == {"event": "end-file", "reason": "eof"}

    client.close()
    peer.close()
    listener.close()


def test_mpv_client_raises_when_the_socket_closes_mid_read(tmp_path):
    socket_path = str(tmp_path / "mpv.sock")

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(socket_path)
    listener.listen(1)

    client = MpvIpcClient(socket_path).connect()

    peer, _ = listener.accept()
    peer.close()

    with pytest.raises(ConnectionError):
        client.read_event()

    client.close()
    listener.close()
