from __future__ import annotations

import json
from pathlib import Path

MEMORY_RECALL_STATE_FILE_GLOB = "memory-recall-*.json"


def read_memory_recall_session_states(state_directory: Path) -> list[dict]:
    if not state_directory.is_dir():
        return []
    session_states = []
    for state_file in sorted(state_directory.glob(MEMORY_RECALL_STATE_FILE_GLOB)):
        try:
            session_states.append(json.loads(state_file.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return session_states


def summarize_memory_recall_savings(session_states: list[dict]) -> dict:
    injected_recall_event_count = 0
    injected_recall_character_total = 0
    dedup_suppressed_character_total = 0
    suppressed_recall_event_count_by_reason: dict[str, int] = {}
    for session_state in session_states:
        injected_recall_event_count += session_state.get("recall_event_count", 0)
        injected_recall_character_total += session_state.get(
            "recall_character_total", 0
        )
        dedup_suppressed_character_total += session_state.get(
            "dedup_suppressed_character_total", 0
        )
        for suppression_reason, suppression_count in session_state.get(
            "suppressed_event_count_by_reason", {}
        ).items():
            suppressed_recall_event_count_by_reason[suppression_reason] = (
                suppressed_recall_event_count_by_reason.get(suppression_reason, 0)
                + suppression_count
            )
    return {
        "memory_recall_session_count": len(session_states),
        "injected_recall_event_count": injected_recall_event_count,
        "injected_recall_character_total": injected_recall_character_total,
        "suppressed_recall_event_total": sum(
            suppressed_recall_event_count_by_reason.values()
        ),
        "suppressed_recall_event_count_by_reason": suppressed_recall_event_count_by_reason,
        "dedup_suppressed_character_total": dedup_suppressed_character_total,
    }


def summarize_memory_recall_savings_in_directory(state_directory: Path) -> dict:
    return summarize_memory_recall_savings(
        read_memory_recall_session_states(state_directory)
    )
