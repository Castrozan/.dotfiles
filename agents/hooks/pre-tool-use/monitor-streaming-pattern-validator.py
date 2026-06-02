#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interactive_command_hang_detectors import (  # noqa: E402
    command_launches_interactive_full_screen_program,
    command_runs_git_subcommand_that_opens_an_editor,
)

STREAMING_PATTERNS_REFERENCE_FILE_PATH = "~/.claude/hooks/monitor-streaming-patterns.md"
HANG_PATTERNS_REFERENCE_FILE_PATH = "~/.claude/hooks/background-bash-anti-patterns.md"

STDERR_HEAVY_COMMAND_PATTERNS = (
    r"\bgit\s+(fetch|push|pull|clone|clean|gc)\b",
    r"\bcurl\s+[^|]*-v",
    r"\bnpm\s+(install|ci|run|update)\b",
    r"\byarn\s+(install|add)\b",
    r"\bpnpm\s+(install|add)\b",
    r"\bcargo\s+(build|test|run|check)\b",
    r"\bmake\b",
    r"\bkubectl\s+\w+\s+.*-v\b",
)


def command_invokes_python_with_buffered_stdout(command_string):
    invokes_python = bool(re.search(r"\bpython3?\b", command_string))
    if not invokes_python:
        return False
    python_call_has_unbuffered_flag = bool(
        re.search(
            r"\bpython3?\b[^|;&\n]*?(?<!\S)-[A-Za-z]*u[A-Za-z]*\b", command_string
        )
    )
    environment_disables_python_buffering = "PYTHONUNBUFFERED=" in command_string
    return not (
        python_call_has_unbuffered_flag or environment_disables_python_buffering
    )


def command_pipes_into_grep_without_line_buffered_flag(command_string):
    pipe_into_grep_pattern = re.compile(
        r"\|\s*(?:[A-Z_]+=\S+\s+)*(?:grep|egrep|fgrep)\b([^|]*)"
    )
    for matched_grep_invocation in pipe_into_grep_pattern.finditer(command_string):
        invocation_flags = matched_grep_invocation.group(1)
        if "--line-buffered" not in invocation_flags:
            return True
    return False


def command_pipes_into_sed_without_unbuffered_flag(command_string):
    pipe_into_sed_pattern = re.compile(r"\|\s*(?:[A-Z_]+=\S+\s+)*sed\b([^|]*)")
    for matched_sed_invocation in pipe_into_sed_pattern.finditer(command_string):
        invocation_flags = matched_sed_invocation.group(1)
        sed_has_unbuffered_flag = bool(
            re.search(r"(?<![A-Za-z0-9])-u\b|--unbuffered\b", invocation_flags)
        )
        if not sed_has_unbuffered_flag:
            return True
    return False


def command_pipes_into_awk(command_string):
    return bool(re.search(r"\|\s*(?:awk|gawk|nawk|mawk)\b", command_string))


def command_runs_known_stderr_heavy_program_without_redirect(command_string):
    if re.search(r"2>&1\b", command_string):
        return False
    return any(
        re.search(pattern, command_string) for pattern in STDERR_HEAVY_COMMAND_PATTERNS
    )


PATTERN_DETECTORS_BY_RULE_NAME = {
    "python-without-u": command_invokes_python_with_buffered_stdout,
    "grep-without-line-buffered": command_pipes_into_grep_without_line_buffered_flag,
    "sed-without-u": command_pipes_into_sed_without_unbuffered_flag,
    "awk-needs-fflush": command_pipes_into_awk,
    "stderr-only-without-redirect": command_runs_known_stderr_heavy_program_without_redirect,
}

HANG_PATTERN_DETECTORS_BY_RULE_NAME = {
    "interactive-editor-or-full-screen-tui": command_launches_interactive_full_screen_program,
    "command-that-opens-an-editor": command_runs_git_subcommand_that_opens_an_editor,
}


def find_streaming_anti_patterns_in_command(command_string):
    return [
        rule_name
        for rule_name, detector in PATTERN_DETECTORS_BY_RULE_NAME.items()
        if detector(command_string)
    ]


def find_hang_anti_patterns_in_command(command_string):
    return [
        rule_name
        for rule_name, detector in HANG_PATTERN_DETECTORS_BY_RULE_NAME.items()
        if detector(command_string)
    ]


def build_deny_reason_message(triggered_streaming_rules, triggered_hang_rules):
    sentences = []
    if triggered_hang_rules:
        hang_rules_list_text = ", ".join(triggered_hang_rules)
        sentences.append(
            f"Monitor runs this command and streams its stdout, but the command "
            f"matches: {hang_rules_list_text}. It blocks forever on a controlling "
            f"terminal that the Monitor process does not have (interactive editor, "
            f"full-screen TUI, or a subcommand that opens an editor), so it never "
            f"produces output or exits. "
            f"Read {HANG_PATTERNS_REFERENCE_FILE_PATH} for the correct invocation "
            f"patterns, then retry."
        )
    if triggered_streaming_rules:
        streaming_rules_list_text = ", ".join(triggered_streaming_rules)
        sentences.append(
            f"Monitor would batch all output into a single end-of-stream "
            f"notification because the command matches: {streaming_rules_list_text}. "
            f"Read {STREAMING_PATTERNS_REFERENCE_FILE_PATH} for the correct "
            f"invocation patterns, then retry."
        )
    return " ".join(sentences)


def emit_deny_decision_for_pre_tool_use_hook(deny_reason_message):
    output_payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": deny_reason_message,
        }
    }
    json.dump(output_payload, sys.stdout)


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if hook_input.get("tool_name") != "Monitor":
        sys.exit(0)

    command_string = hook_input.get("tool_input", {}).get("command", "")
    if not command_string:
        sys.exit(0)

    triggered_streaming_rules = find_streaming_anti_patterns_in_command(command_string)
    triggered_hang_rules = find_hang_anti_patterns_in_command(command_string)
    if not triggered_streaming_rules and not triggered_hang_rules:
        sys.exit(0)

    emit_deny_decision_for_pre_tool_use_hook(
        build_deny_reason_message(triggered_streaming_rules, triggered_hang_rules)
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
