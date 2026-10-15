import json
import socket
import subprocess

import pytest

from ambient_canvas_mpv_visibility import (
    VisibilityGatedPlaybackController,
    resolve_player_visibility,
)
from mpv_ambient_canvas_ipc import MpvIpcClient


def test_visibility_controller_pauses_when_canvas_is_outside_viewport(monkeypatch):
    sent_commands = []

    class RecordingClient:
        def send_command(self, command):
            sent_commands.append(command)

    responses = {
        "activeworkspace": {"id": 11},
        "clients": [
            {
                "pid": 14534,
                "workspace": {"id": 11},
                "at": [2, -1078],
                "size": [1916, 1076],
                "mapped": True,
                "hidden": False,
            }
        ],
        "monitors": [
            {
                "id": 0,
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "scale": 1,
                "activeWorkspace": {"id": 11},
            }
        ],
    }
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.subprocess.run",
        lambda command, **kwargs: type(
            "Completed", (), {"stdout": json.dumps(responses[command[-1]])}
        )(),
    )
    controller = VisibilityGatedPlaybackController(RecordingClient(), 14534, 11)
    controller._synchronize_with_visibility()
    assert sent_commands == [["set_property", "pause", "yes"]]


@pytest.mark.parametrize("response", ["{}", "null", "broken", "[{}]"])
def test_malformed_compositor_state_pauses(monkeypatch, response):
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed", (), {"stdout": response, "returncode": 0}
        )(),
    )
    assert not resolve_player_visibility(14534, 11)


@pytest.mark.parametrize(
    "error", [FileNotFoundError("hyprctl"), subprocess.TimeoutExpired("hyprctl", 1)]
)
def test_compositor_failure_pauses(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr("ambient_canvas_mpv_visibility.subprocess.run", fail)
    assert not resolve_player_visibility(14534, 11)


def test_visibility_controller_pauses_when_target_workspace_is_not_active(monkeypatch):
    sent_commands = []

    class RecordingClient:
        def send_command(self, command):
            sent_commands.append(command)

    controller = VisibilityGatedPlaybackController(RecordingClient(), 14534, 11)
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.resolve_player_visibility", lambda *args: False
    )
    controller._synchronize_with_visibility()
    assert sent_commands == [["set_property", "pause", "yes"]]


def test_visibility_controller_resumes_when_target_workspace_is_active(monkeypatch):
    sent_commands = []

    class RecordingClient:
        def send_command(self, command):
            sent_commands.append(command)

    controller = VisibilityGatedPlaybackController(RecordingClient(), 14534, 11)
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.resolve_player_visibility", lambda *args: True
    )
    controller._synchronize_with_visibility()
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


def test_visibility_controller_sends_only_transitions_and_pauses_on_unknown(
    monkeypatch,
):
    sent_commands = []

    class RecordingClient:
        def send_command(self, command):
            sent_commands.append(command)

    visibility = iter([True, True, False, False, False, True])
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.resolve_player_visibility",
        lambda *args: next(visibility),
    )
    controller = VisibilityGatedPlaybackController(RecordingClient(), 14534, 11)
    for _ in range(6):
        controller._synchronize_with_visibility()
    assert sent_commands == [
        ["set_property", "pause", "no"],
        ["set_property", "pause", "yes"],
        ["set_property", "pause", "no"],
    ]


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
