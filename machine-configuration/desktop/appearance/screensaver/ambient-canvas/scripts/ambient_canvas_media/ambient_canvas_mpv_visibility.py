import json
import subprocess
import threading

from playback.player_visibility_geometry import player_is_visible

VISIBILITY_POLL_INTERVAL_SECONDS = 1.0

HIDDEN_PLAYER_COMMANDS = (
    ["set_property", "pause", "yes"],
    ["set_property", "force-window", "no"],
    ["set_property", "vid", "no"],
)
VISIBLE_PLAYER_COMMANDS = (
    ["set_property", "vid", "auto"],
    ["set_property", "force-window", "yes"],
    ["set_property", "pause", "no"],
)


def resolve_player_visibility(player_process_id, target_workspace_id):
    try:
        snapshots = []
        for subject in ("clients", "monitors"):
            completed = subprocess.run(
                ["hyprctl", "-j", subject],
                capture_output=True,
                text=True,
                check=True,
                timeout=1,
            )
            snapshot = json.loads(completed.stdout)
            if not isinstance(snapshot, list):
                return False
            snapshots.append(snapshot)
        return player_is_visible(*snapshots, player_process_id, target_workspace_id)
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
    ):
        return False


class VisibilityGatedPlaybackController:
    def __init__(self, mpv_client, player_process_id, target_workspace_id):
        self.mpv_client = mpv_client
        self.player_process_id = player_process_id
        self.target_workspace_id = target_workspace_id
        self._previous_should_play = None
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._watch_visibility, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=3)

    def _watch_visibility(self):
        while not self._stop_event.is_set():
            self._synchronize_with_visibility()
            self._stop_event.wait(VISIBILITY_POLL_INTERVAL_SECONDS)

    def _synchronize_with_visibility(self):
        should_play = resolve_player_visibility(
            self.player_process_id, self.target_workspace_id
        )
        if should_play == self._previous_should_play:
            return
        for command in (
            VISIBLE_PLAYER_COMMANDS if should_play else HIDDEN_PLAYER_COMMANDS
        ):
            self.mpv_client.send_command(command)
        self._previous_should_play = should_play
