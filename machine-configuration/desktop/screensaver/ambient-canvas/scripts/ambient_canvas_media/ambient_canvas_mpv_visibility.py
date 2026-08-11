import json
import subprocess
import threading
import time

VISIBILITY_POLL_INTERVAL_SECONDS = 1.0
HYPRCTL_ACTIVE_WORKSPACE_COMMAND = ["hyprctl", "-j", "activeworkspace"]
PLAYER_WINDOW_TITLE = "ambient-canvas-gpu-screensaver"
WINDOW_MAP_WAIT_ATTEMPTS = 40
WINDOW_MAP_WAIT_INTERVAL_SECONDS = 0.25
WINDOW_PIN_RETRY_ATTEMPTS = 10
WINDOW_PIN_RETRY_INTERVAL_SECONDS = 1.0


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


def run_hyprctl_command(dispatch_arguments):
    try:
        subprocess.run(
            ["hyprctl", "dispatch", *dispatch_arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def window_is_mapped():
    try:
        completed = subprocess.run(
            ["hyprctl", "-j", "clients"],
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    try:
        clients = json.loads(completed.stdout)
    except (ValueError, AttributeError):
        return False
    return any(
        client.get("title") == PLAYER_WINDOW_TITLE and client.get("mapped")
        for client in clients
    )


def pin_player_window_to_workspace():
    for _ in range(WINDOW_MAP_WAIT_ATTEMPTS):
        if window_is_mapped():
            break
        time.sleep(WINDOW_MAP_WAIT_INTERVAL_SECONDS)
    for _ in range(WINDOW_PIN_RETRY_ATTEMPTS):
        run_hyprctl_command(["focuswindow", f"title:^{PLAYER_WINDOW_TITLE}$"])
        run_hyprctl_command(["fullscreen"])
        time.sleep(WINDOW_PIN_RETRY_INTERVAL_SECONDS)
        if window_is_fullscreen():
            return


def window_is_fullscreen():
    try:
        completed = subprocess.run(
            ["hyprctl", "-j", "clients"],
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    try:
        clients = json.loads(completed.stdout)
    except (ValueError, AttributeError):
        return False
    return any(
        client.get("title") == PLAYER_WINDOW_TITLE and client.get("fullscreen")
        for client in clients
    )


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
