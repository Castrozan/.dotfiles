#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from streamed_command_anti_pattern_detectors import (  # noqa: E402, F401
    command_invokes_python_with_buffered_stdout,
    command_pipes_into_awk,
    command_pipes_into_grep_without_line_buffered_flag,
    command_pipes_into_sed_without_unbuffered_flag,
    command_runs_known_stderr_heavy_program_without_redirect,
    find_busy_wait_anti_patterns_in_command,
    find_hang_anti_patterns_in_command,
    find_streaming_anti_patterns_in_command,
)

STREAMING_PATTERNS_REFERENCE_FILE_PATH = "~/.claude/hooks/monitor-streaming-patterns.md"
HANG_PATTERNS_REFERENCE_FILE_PATH = "~/.claude/hooks/background-bash-anti-patterns.md"


def streamed_execution_context_label_for_tool(tool_name):
    if tool_name == "Bash":
        return "The backgrounded Bash command"
    return "Monitor"


def command_runs_in_a_streamed_or_backgrounded_context(tool_name, tool_input):
    if tool_name == "Monitor":
        return True
    return tool_name == "Bash" and tool_input.get("run_in_background") is True


def build_deny_reason_message(
    triggered_streaming_rules,
    triggered_hang_rules,
    triggered_busy_wait_rules,
    streamed_execution_context_label,
):
    sentences = []
    if triggered_busy_wait_rules:
        busy_wait_rules_list_text = ", ".join(triggered_busy_wait_rules)
        sentences.append(
            f"{streamed_execution_context_label} matches: {busy_wait_rules_list_text}. "
            f"A shell loop that calls sleep busy-waits and emits nothing until it "
            f"exits, so it looks stuck and burns wall-clock polling. Wait on the "
            f"actual condition with Monitor and an until-loop, or background the real "
            f"work and let its completion notify you, instead of a for/while/until "
            f"plus sleep poll. "
            f"Read {HANG_PATTERNS_REFERENCE_FILE_PATH} for the correct invocation "
            f"patterns, then retry."
        )
    if triggered_hang_rules:
        hang_rules_list_text = ", ".join(triggered_hang_rules)
        sentences.append(
            f"{streamed_execution_context_label} runs this command and streams its "
            f"stdout, but the command matches: {hang_rules_list_text}. It blocks "
            f"forever on a controlling terminal that the background process does not "
            f"have (interactive editor, full-screen TUI, or a subcommand that opens "
            f"an editor), so it never produces output or exits. "
            f"Read {HANG_PATTERNS_REFERENCE_FILE_PATH} for the correct invocation "
            f"patterns, then retry."
        )
    if triggered_streaming_rules:
        streaming_rules_list_text = ", ".join(triggered_streaming_rules)
        sentences.append(
            f"{streamed_execution_context_label} would batch all output into a single "
            f"end-of-stream notification because the command matches: "
            f"{streaming_rules_list_text}. "
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

    tool_name = hook_input.get("tool_name")
    tool_input = hook_input.get("tool_input", {})
    if not command_runs_in_a_streamed_or_backgrounded_context(tool_name, tool_input):
        sys.exit(0)

    command_string = tool_input.get("command", "")
    if not command_string:
        sys.exit(0)

    triggered_streaming_rules = find_streaming_anti_patterns_in_command(command_string)
    triggered_hang_rules = find_hang_anti_patterns_in_command(command_string)
    triggered_busy_wait_rules = find_busy_wait_anti_patterns_in_command(command_string)
    if not (
        triggered_streaming_rules or triggered_hang_rules or triggered_busy_wait_rules
    ):
        sys.exit(0)

    emit_deny_decision_for_pre_tool_use_hook(
        build_deny_reason_message(
            triggered_streaming_rules,
            triggered_hang_rules,
            triggered_busy_wait_rules,
            streamed_execution_context_label_for_tool(tool_name),
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
