from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402
from memory_recall_debounce import (  # noqa: E402
    SUPPRESSION_REASON_BUDGET,
    SUPPRESSION_REASON_DEBOUNCE,
    SUPPRESSION_REASON_DEDUP,
    debounce_state_path_for_session,
    exclusive_session_state_lock,
    has_recall_session_budget_been_exhausted,
    load_debounce_state,
    persist_debounce_state,
    record_recall_injection,
    record_recall_suppression,
    should_skip_due_to_debounce,
    was_recall_path_set_already_injected,
)
from memory_recall_io import format_recall_context  # noqa: E402
from memory_recall_keywords import (  # noqa: E402
    collect_strings_from_tool_input,
    extract_keywords_from_text,
)
from memory_recall_memory_directory import (  # noqa: E402
    resolve_memory_directory_for_cwd,
)
from memory_recall_ripgrep import (  # noqa: E402
    ripgrep_score_per_file,
    select_top_recall_paths,
)


class _RecallSuppressed(Exception):
    pass


def _claim_recall_slot(state_path, keywords: list[str]) -> None:
    with exclusive_session_state_lock(state_path):
        state = load_debounce_state(state_path)
        if has_recall_session_budget_been_exhausted(state):
            record_recall_suppression(state_path, SUPPRESSION_REASON_BUDGET)
            raise _RecallSuppressed
        if should_skip_due_to_debounce(state, set(keywords)):
            record_recall_suppression(state_path, SUPPRESSION_REASON_DEBOUNCE)
            raise _RecallSuppressed
        persist_debounce_state(state_path, keywords)


def _guard_recall_injection(
    state_path, recall_path_identifiers: list[str], recall_context: str
) -> None:
    with exclusive_session_state_lock(state_path):
        state = load_debounce_state(state_path)
        if was_recall_path_set_already_injected(state, recall_path_identifiers):
            record_recall_suppression(
                state_path, SUPPRESSION_REASON_DEDUP, len(recall_context)
            )
            raise _RecallSuppressed
        record_recall_injection(
            state_path, recall_path_identifiers, len(recall_context)
        )


def handle(hook_input):
    cwd = hook_input.get("cwd", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "")

    memory_directory = resolve_memory_directory_for_cwd(cwd)
    if not memory_directory.is_dir():
        return None

    tool_input_text = collect_strings_from_tool_input(tool_input)
    keywords = extract_keywords_from_text(tool_input_text)
    if not keywords:
        return None

    state_path = debounce_state_path_for_session(session_id)
    try:
        _claim_recall_slot(state_path, keywords)

        scores = ripgrep_score_per_file(memory_directory, keywords)
        if not scores:
            return None

        recall_paths = select_top_recall_paths(scores)
        if not recall_paths:
            return None

        recall_path_identifiers = [str(path.resolve()) for path in recall_paths]
        recall_context = format_recall_context(recall_paths, memory_directory)
        _guard_recall_injection(state_path, recall_path_identifiers, recall_context)
    except _RecallSuppressed:
        return None
    return HandlerResult(additional_context=recall_context)
