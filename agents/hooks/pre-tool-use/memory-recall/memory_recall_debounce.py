from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path

STATE_LOCK_ACQUISITION_TIMEOUT_SECONDS = 2.0
STATE_LOCK_RETRY_INTERVAL_SECONDS = 0.01

DEBOUNCE_SECONDS = 30
DEBOUNCE_HARD_FLOOR_SECONDS = 15
DEBOUNCE_KEYWORD_OVERLAP_THRESHOLD = 0.5
SESSION_RECALL_EVENT_BUDGET = 40
SESSION_RECALL_CHARACTER_BUDGET = 20000

SUPPRESSION_REASON_BUDGET = "budget"
SUPPRESSION_REASON_DEBOUNCE = "debounce"
SUPPRESSION_REASON_DEDUP = "dedup"


def resolve_debounce_state_directory() -> Path:
    override = os.environ.get("MEMORY_RECALL_DEBOUNCE_STATE_DIRECTORY")
    if override:
        return Path(override)
    return Path("/tmp")


def debounce_state_path_for_session(session_id: str) -> Path:
    safe_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    return resolve_debounce_state_directory() / f"memory-recall-{safe_session_id}.json"


def state_lock_path_for_session_state(state_path: Path) -> Path:
    return state_path.with_name(f"{state_path.name}.lock")


def acquire_exclusive_lock_before_deadline(lock_file) -> bool:
    deadline = time.time() + STATE_LOCK_ACQUISITION_TIMEOUT_SECONDS
    while True:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            if time.time() >= deadline:
                return False
            time.sleep(STATE_LOCK_RETRY_INTERVAL_SECONDS)


@contextmanager
def exclusive_session_state_lock(state_path: Path):
    lock_path = state_lock_path_for_session_state(state_path)
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = lock_path.open("w")
    except OSError:
        yield
        return
    try:
        acquire_exclusive_lock_before_deadline(lock_file)
        yield
    finally:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
        except OSError:
            pass
        lock_file.close()


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
    state = load_debounce_state(state_path)
    state["last_fire_timestamp"] = time.time()
    state["last_keywords"] = current_keywords
    write_debounce_state(state_path, state)


def write_debounce_state(state_path: Path, state: dict) -> None:
    staging_path = state_path.with_name(f"{state_path.name}.{os.getpid()}.staging")
    try:
        staging_path.write_text(json.dumps(state))
        os.replace(staging_path, state_path)
    except OSError:
        try:
            staging_path.unlink()
        except OSError:
            pass


def hash_recall_path_set(recall_path_identifiers: list[str]) -> str:
    canonical_path_set = "\n".join(sorted(recall_path_identifiers))
    return hashlib.sha1(canonical_path_set.encode("utf-8")).hexdigest()


def has_recall_session_budget_been_exhausted(state: dict) -> bool:
    if state.get("recall_event_count", 0) >= SESSION_RECALL_EVENT_BUDGET:
        return True
    return state.get("recall_character_total", 0) >= SESSION_RECALL_CHARACTER_BUDGET


def was_recall_path_set_already_injected(
    state: dict, recall_path_identifiers: list[str]
) -> bool:
    already_injected_hashes = state.get("injected_recall_path_set_hashes", [])
    return hash_recall_path_set(recall_path_identifiers) in already_injected_hashes


def record_recall_injection(
    state_path: Path,
    recall_path_identifiers: list[str],
    injected_character_count: int,
) -> None:
    state = load_debounce_state(state_path)
    path_set_hash = hash_recall_path_set(recall_path_identifiers)
    already_injected_hashes = state.get("injected_recall_path_set_hashes", [])
    if path_set_hash not in already_injected_hashes:
        already_injected_hashes.append(path_set_hash)
    state["injected_recall_path_set_hashes"] = already_injected_hashes
    state["recall_event_count"] = state.get("recall_event_count", 0) + 1
    state["recall_character_total"] = (
        state.get("recall_character_total", 0) + injected_character_count
    )
    write_debounce_state(state_path, state)


def record_recall_suppression(
    state_path: Path,
    suppression_reason: str,
    would_have_injected_character_count: int = 0,
) -> None:
    state = load_debounce_state(state_path)
    suppressed_counts_by_reason = state.get("suppressed_event_count_by_reason", {})
    suppressed_counts_by_reason[suppression_reason] = (
        suppressed_counts_by_reason.get(suppression_reason, 0) + 1
    )
    state["suppressed_event_count_by_reason"] = suppressed_counts_by_reason
    state["dedup_suppressed_character_total"] = (
        state.get("dedup_suppressed_character_total", 0)
        + would_have_injected_character_count
    )
    write_debounce_state(state_path, state)
