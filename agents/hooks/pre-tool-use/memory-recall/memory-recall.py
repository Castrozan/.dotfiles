#!/usr/bin/env python3
"""PreToolUse hook: associative recall from the cwd-derived memory directory.

Reads the standard Claude Code hook JSON from stdin. Computes the
memory directory the same way memory-write does (every '/' and '.'
in the absolute cwd is replaced with '-', then ~/.claude/projects/
<encoded>/memory/ is the target). If the directory does not exist,
exits silently because this cwd has no memory wiring.

Extracts keywords from the tool input text, ripgreps the memory
directory for matching files, scores each file by how many distinct
keywords matched, and emits the top hits as 'Recall: @path1 @path2
...' through hookSpecificOutput.additionalContext. A per-session
state file under /tmp debounces repeat fires so that a multi-tool
turn does not flood the same recall into context.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from memory_recall_debounce import (  # noqa: E402, F401
    DEBOUNCE_HARD_FLOOR_SECONDS,
    DEBOUNCE_KEYWORD_OVERLAP_THRESHOLD,
    DEBOUNCE_SECONDS,
    SESSION_RECALL_CHARACTER_BUDGET,
    SESSION_RECALL_EVENT_BUDGET,
    debounce_state_path_for_session,
    has_recall_session_budget_been_exhausted,
    hash_recall_path_set,
    load_debounce_state,
    persist_debounce_state,
    record_recall_injection,
    resolve_debounce_state_directory,
    should_skip_due_to_debounce,
    was_recall_path_set_already_injected,
)
from memory_recall_io import (  # noqa: E402, F401
    emit_additional_context_and_exit,
    exit_silently,
    format_recall_context,
    read_hook_input_from_stdin,
)
from memory_recall_keywords import (  # noqa: E402, F401
    ALL_STOP_WORDS,
    ENGLISH_STOP_WORDS,
    MAX_KEYWORDS,
    MIN_KEYWORD_LENGTH,
    PORTUGUESE_STOP_WORDS,
    collect_strings_from_tool_input,
    extract_keywords_from_text,
)
from memory_recall_memory_directory import (  # noqa: E402, F401
    encode_cwd_as_claude_project_directory,
    resolve_memory_directory_for_cwd,
)
from memory_recall_ripgrep import (  # noqa: E402, F401
    MAX_RECALL_PATHS,
    ripgrep_score_per_file,
    select_top_recall_paths,
)


def main() -> None:
    hook_input = read_hook_input_from_stdin()
    cwd = hook_input.get("cwd", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "")

    memory_directory = resolve_memory_directory_for_cwd(cwd)
    if not memory_directory.is_dir():
        exit_silently()

    tool_input_text = collect_strings_from_tool_input(tool_input)
    keywords = extract_keywords_from_text(tool_input_text)
    if not keywords:
        exit_silently()

    state_path = debounce_state_path_for_session(session_id)
    state = load_debounce_state(state_path)
    if has_recall_session_budget_been_exhausted(state):
        exit_silently()
    if should_skip_due_to_debounce(state, set(keywords)):
        exit_silently()

    scores = ripgrep_score_per_file(memory_directory, keywords)
    if not scores:
        persist_debounce_state(state_path, keywords)
        exit_silently()

    recall_paths = select_top_recall_paths(scores)
    if not recall_paths:
        persist_debounce_state(state_path, keywords)
        exit_silently()

    recall_path_identifiers = [str(path.resolve()) for path in recall_paths]
    if was_recall_path_set_already_injected(state, recall_path_identifiers):
        persist_debounce_state(state_path, keywords)
        exit_silently()

    recall_context = format_recall_context(recall_paths, memory_directory)
    persist_debounce_state(state_path, keywords)
    record_recall_injection(state_path, recall_path_identifiers, len(recall_context))
    emit_additional_context_and_exit(recall_context)


if __name__ == "__main__":
    main()
