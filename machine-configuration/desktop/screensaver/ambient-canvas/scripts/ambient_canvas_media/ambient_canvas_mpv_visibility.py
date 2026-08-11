import json
import subprocess
import threading

VISIBILITY_POLL_INTERVAL_SECONDS = 1.0
HYPRCTL_ACTIVE_WORKSPACE_COMMAND = ["hyprctl", "-j", "activeworkspace"]


def resolve_active_workspace_id():
    try:
        completed = subprocess.run(
            HYPRCTL_ACTIVE_WORKSPACE_COMMAND,
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    try:
        return json.loads(completed.stdout).get("id")
    except (ValueError, AttributeError):
        return None


class VisibilityGatedPlaybackController:
    def __init__(self, mpv_client, target_workspace_id):
        self.mpv_client = mpv_client
        self.target_workspace_id = target_workspace_id
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._watch_workspace_visibility, daemon=True
        )

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=2)

    def _watch_workspace_visibility(self):
        while not self._stop_event.is_set():
            self._synchronize_with_active_workspace()
            self._stop_event.wait(VISIBILITY_POLL_INTERVAL_SECONDS)

    def _synchronize_with_active_workspace(self):
        active_workspace_id = resolve_active_workspace_id()
        should_play = active_workspace_id == self.target_workspace_id
        self.mpv_client.send_command(
            ["set_property", "pause", "no" if should_play else "yes"]
        )
