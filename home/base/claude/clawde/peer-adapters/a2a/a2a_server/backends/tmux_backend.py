import re
import subprocess
import time

from .base import AgentBackend, BackendObservation

PANE_CAPTURE_LINE_COUNT = 200
DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS = 0.25


class TmuxAttachedAgentBackend(AgentBackend):
    def __init__(
        self,
        tmux_session_name: str,
        tmux_window_name: str,
        meaningful_line_pattern: re.Pattern | None = None,
    ) -> None:
        self._tmux_session_name = tmux_session_name
        self._tmux_window_name = tmux_window_name
        self._meaningful_line_pattern = meaningful_line_pattern
        self._previously_observed_meaningful_line_occurrence_keys: set[
            tuple[str, int]
        ] = set()
        self._last_activity_at_epoch_seconds = time.time()

    def start(self) -> None:
        if not self._target_tmux_window_exists():
            raise RuntimeError(
                f"tmux target {self._target_specifier()!r} does not exist; "
                "the backend attaches to an already-running window"
            )
        initial_capture_text = self._capture_pane_text()
        self._previously_observed_meaningful_line_occurrence_keys = set(
            self._extract_meaningful_line_occurrence_keys_in_capture_order(
                initial_capture_text
            )
        )

    def send_input_text(self, text: str) -> None:
        self._run_tmux_command(
            ["send-keys", "-t", self._target_specifier(), "-l", text]
        )
        time.sleep(DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS)
        self._run_tmux_command(["send-keys", "-t", self._target_specifier(), "Enter"])
        self._last_activity_at_epoch_seconds = time.time()

    def observe(self) -> BackendObservation:
        current_capture_text = self._capture_pane_text()
        current_occurrence_keys_in_order = list(
            self._extract_meaningful_line_occurrence_keys_in_capture_order(
                current_capture_text
            )
        )
        current_occurrence_keys_as_set = set(current_occurrence_keys_in_order)
        newly_appeared_occurrence_keys = (
            current_occurrence_keys_as_set
            - self._previously_observed_meaningful_line_occurrence_keys
        )
        new_lines_in_capture_order = [
            line
            for (line, _occurrence_index) in current_occurrence_keys_in_order
            if (line, _occurrence_index) in newly_appeared_occurrence_keys
        ]
        if new_lines_in_capture_order:
            self._last_activity_at_epoch_seconds = time.time()
        self._previously_observed_meaningful_line_occurrence_keys = (
            current_occurrence_keys_as_set
        )
        return BackendObservation(
            raw_output_since_last_call="\n".join(new_lines_in_capture_order),
            is_alive=self._target_tmux_window_exists(),
            last_activity_at_epoch_seconds=self._last_activity_at_epoch_seconds,
        )

    def cancel_gracefully(self) -> None:
        self._run_tmux_command(["send-keys", "-t", self._target_specifier(), "C-c"])

    def stop(self) -> None:
        self._run_tmux_command(["kill-window", "-t", self._target_specifier()])

    def _target_specifier(self) -> str:
        return f"{self._tmux_session_name}:{self._tmux_window_name}"

    def _target_tmux_window_exists(self) -> bool:
        result = self._run_tmux_command(
            ["list-windows", "-t", self._tmux_session_name, "-F", "#{window_name}"]
        )
        if result.returncode != 0:
            return False
        return self._tmux_window_name in result.stdout.splitlines()

    def _capture_pane_text(self) -> str:
        result = self._run_tmux_command(
            [
                "capture-pane",
                "-p",
                "-J",
                "-t",
                self._target_specifier(),
                "-S",
                f"-{PANE_CAPTURE_LINE_COUNT}",
            ]
        )
        if result.returncode != 0:
            return ""
        return result.stdout

    def _run_tmux_command(self, arguments: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["tmux", *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def _extract_meaningful_line_occurrence_keys_in_capture_order(
        self, capture_text: str
    ):
        per_line_occurrence_counters: dict[str, int] = {}
        for raw_line in capture_text.splitlines():
            normalized = raw_line.strip()
            if not normalized:
                continue
            if (
                self._meaningful_line_pattern is not None
                and not self._meaningful_line_pattern.search(normalized)
            ):
                continue
            occurrence_index_for_this_line = per_line_occurrence_counters.get(
                normalized, 0
            )
            yield (normalized, occurrence_index_for_this_line)
            per_line_occurrence_counters[normalized] = (
                occurrence_index_for_this_line + 1
            )
