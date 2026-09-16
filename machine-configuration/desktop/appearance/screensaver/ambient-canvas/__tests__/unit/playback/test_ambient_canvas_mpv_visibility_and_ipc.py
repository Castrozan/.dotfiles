import json
import socket

import pytest

from ambient_canvas_mpv_visibility import (
    VisibilityGatedPlaybackController,
    resolve_active_workspace_id,
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
