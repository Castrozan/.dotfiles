from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

DEBOUNCE_SECONDS = 30
DEBOUNCE_HARD_FLOOR_SECONDS = 15
DEBOUNCE_KEYWORD_OVERLAP_THRESHOLD = 0.5


def resolve_debounce_state_directory() -> Path:
    override = os.environ.get("MEMORY_RECALL_DEBOUNCE_STATE_DIRECTORY")
    if override:
        return Path(override)
    return Path("/tmp")


def debounce_state_path_for_session(session_id: str) -> Path:
    safe_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    return resolve_debounce_state_directory() / f"memory-recall-{safe_session_id}.json"


def load_debounce_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def should_skip_due_to_debounce(state: dict, current_keywords: set[str]) -> bool:
    if not state:
        return False
    elapsed_seconds = time.time() - state.get("last_fire_timestamp", 0)
    if elapsed_seconds > DEBOUNCE_SECONDS:
        return False
    if elapsed_seconds <= DEBOUNCE_HARD_FLOOR_SECONDS:
        return True
    last_keywords = set(state.get("last_keywords", []))
    if not current_keywords or not last_keywords:
        return False
    overlap_ratio = len(current_keywords & last_keywords) / len(current_keywords)
    return overlap_ratio >= DEBOUNCE_KEYWORD_OVERLAP_THRESHOLD


def persist_debounce_state(state_path: Path, current_keywords: list[str]) -> None:
    try:
        state_path.write_text(
            json.dumps(
                {
                    "last_fire_timestamp": time.time(),
                    "last_keywords": current_keywords,
                }
            )
        )
    except OSError:
        pass
