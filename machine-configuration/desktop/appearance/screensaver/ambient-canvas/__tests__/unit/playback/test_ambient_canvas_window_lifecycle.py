from copy import deepcopy
import json
import subprocess

from ambient_canvas_mpv_visibility import VisibilityGatedPlaybackController


def test_offscreen_player_does_not_remap_over_another_window(monkeypatch):
    player = {
        "pid": 14534,
        "workspace": {"id": 11},
        "at": [2, -1078],
        "size": [1916, 1076],
        "mapped": True,
        "hidden": False,
    }
    snapshots = {
        "clients": [player, {**player, "pid": 90000, "at": [2, 2]}],
        "monitors": [
            {
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "scale": 1,
                "activeWorkspace": {"id": 11},
            }
        ],
    }
    original_clients = deepcopy(snapshots["clients"])
    monkeypatch.setattr(
        "ambient_canvas_mpv_visibility.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, stdout=json.dumps(snapshots[command[-1]])
        ),
    )

    class WindowLifecycleClient:
        force_window = True

        def send_command(self, command):
            _, name, value = command
            if name == "force-window":
                self.force_window = value == "yes"
            if name == "vid" and value == "no" and not self.force_window:
                snapshots["clients"].remove(player)
            if name == "vid" and value == "auto" and player not in snapshots["clients"]:
                player["at"] = [2, 2]
                snapshots["clients"].append(player)

    controller = VisibilityGatedPlaybackController(WindowLifecycleClient(), 14534, 11)
    for _ in range(4):
        controller._synchronize_with_visibility()
    assert snapshots["clients"] == original_clients
