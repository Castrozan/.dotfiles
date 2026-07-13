import re
import subprocess
import time

from .base import AgentBackend, BackendObservation

PANE_CAPTURE_LINE_COUNT = 200
DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS = 0.25


class HerdrAttachedAgentBackend(AgentBackend):
    def __init__(
        self,
        herdr_pane_id: str,
        meaningful_line_pattern: re.Pattern | None = None,
    ) -> None:
        self._herdr_pane_id = herdr_pane_id
        self._meaningful_line_pattern = meaningful_line_pattern
        self._previously_observed_meaningful_line_occurrence_keys: set[
            tuple[str, int]
        ] = set()
        self._last_activity_at_epoch_seconds = time.time()

    def start(self) -> None:
        if not self._target_herdr_pane_exists():
            raise RuntimeError(
                f"herdr pane {self._herdr_pane_id!r} does not exist; "
                "the backend attaches to an already-running pane"
            )
        initial_capture_text = self._capture_pane_text()
        self._previously_observed_meaningful_line_occurrence_keys = set(
            self._extract_meaningful_line_occurrence_keys_in_capture_order(
                initial_capture_text
            )
        )

    def send_input_text(self, text: str) -> None:
        self._run_herdr_command(["pane", "send-text", self._herdr_pane_id, text])
        time.sleep(DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS)
        self._run_herdr_command(["pane", "send-keys", self._herdr_pane_id, "Enter"])
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
            is_alive=self._target_herdr_pane_exists(),
            last_activity_at_epoch_seconds=self._last_activity_at_epoch_seconds,
        )

    def cancel_gracefully(self) -> None:
        self._run_herdr_command(["pane", "send-keys", self._herdr_pane_id, "C-c"])

    def stop(self) -> None:
        self._run_herdr_command(["pane", "close", self._herdr_pane_id])

    def _target_herdr_pane_exists(self) -> bool:
        result = self._run_herdr_command(["pane", "get", self._herdr_pane_id])
        return result.returncode == 0

    def _capture_pane_text(self) -> str:
        result = self._run_herdr_command(
            [
                "pane",
                "read",
                self._herdr_pane_id,
                "--source",
                "recent-unwrapped",
                "--lines",
                str(PANE_CAPTURE_LINE_COUNT),
            ]
        )
        if result.returncode != 0:
            return ""
        return result.stdout

    def _run_herdr_command(self, arguments: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["herdr", *arguments],
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
