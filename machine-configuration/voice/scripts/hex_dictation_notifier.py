import json
import queue
import subprocess
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass

NOTIFICATION_REFRESH_SECONDS = 20
ENDING_PHASES = {"pasted", "printed", "discarded", "cancelled", "voice_action"}

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess]


@dataclass(frozen=True)
class Notification:
    title: str
    body: str
    urgency: str


RECORDING = Notification("Hex recording", "Release the keys to transcribe", "critical")
TRANSCRIBING = Notification("Hex transcribing", "", "normal")


def run_command(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def read_dictation_phase(event_line: str) -> str | dict | None:
    try:
        event = json.loads(event_line)
    except json.JSONDecodeError:
        return None
    if not isinstance(event, dict) or event.get("kind") != "dictation":
        return None
    return event.get("phase")


class DictationNotifier:
    def __init__(self, command_runner: CommandRunner):
        self._command_runner = command_runner
        self._notification_id = 0
        self._recording = False
        self._phase_handlers = {
            "started": self._begin_recording,
            "transcribing": self._begin_transcribing,
            **dict.fromkeys(ENDING_PHASES, self._end_dictation),
        }

    @property
    def refresh_timeout_seconds(self) -> float | None:
        return NOTIFICATION_REFRESH_SECONDS if self._recording else None

    def handle_event(self, event_line: str) -> None:
        phase = read_dictation_phase(event_line)
        if isinstance(phase, dict):
            self._show_failure(phase)
        elif phase in self._phase_handlers:
            self._phase_handlers[phase]()

    def refresh(self) -> None:
        self._show(RECORDING)

    def _begin_recording(self) -> None:
        self._recording = True
        self._show(RECORDING)

    def _begin_transcribing(self) -> None:
        self._recording = False
        self._show(TRANSCRIBING)

    def _end_dictation(self) -> None:
        self._recording = False
        self._close()

    def _show_failure(self, phase: dict) -> None:
        if "failed" not in phase:
            return
        self._recording = False
        self._show(Notification("Hex dictation failed", phase["failed"], "critical"))

    def _show(self, notification: Notification) -> None:
        result = self._command_runner(
            [
                "notify-send",
                "--app-name=Hex",
                f"--urgency={notification.urgency}",
                "--print-id",
                f"--replace-id={self._notification_id}",
                notification.title,
                notification.body,
            ]
        )
        if result.returncode == 0:
            self._notification_id = int(result.stdout)

    def _close(self) -> None:
        if self._notification_id == 0:
            return
        self._command_runner(
            [
                "busctl",
                "--user",
                "call",
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
                "org.freedesktop.Notifications",
                "CloseNotification",
                "u",
                str(self._notification_id),
            ]
        )
        self._notification_id = 0


def forward_lines(stream, lines: queue.Queue) -> None:
    for line in stream:
        lines.put(line)
    lines.put(None)


def follow_dictation_events(
    event_source_command: list[str], notifier: DictationNotifier
) -> int:
    lines: queue.Queue = queue.Queue()
    with subprocess.Popen(
        event_source_command, stdout=subprocess.PIPE, text=True
    ) as event_source:
        threading.Thread(
            target=forward_lines, args=(event_source.stdout, lines), daemon=True
        ).start()
        while True:
            try:
                line = lines.get(timeout=notifier.refresh_timeout_seconds)
            except queue.Empty:
                notifier.refresh()
                continue
            if line is None:
                return 1
            notifier.handle_event(line)


def main() -> int:
    event_log_path = sys.argv[1]
    return follow_dictation_events(
        ["tail", "-n0", "-F", event_log_path], DictationNotifier(run_command)
    )


if __name__ == "__main__":
    sys.exit(main())
