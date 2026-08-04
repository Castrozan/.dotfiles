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
from shell_read_only_inspection_command import (  # noqa: E402
    command_text_outside_inert_heredoc_bodies,
    command_text_the_shell_executes,
)
from streamed_command_anti_pattern_detectors import (  # noqa: E402
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


def handle(hook_input):
    tool_name = hook_input.get("tool_name")
    tool_input = hook_input.get("tool_input", {})
    if not command_runs_in_a_streamed_or_backgrounded_context(tool_name, tool_input):
        return None

    command_string = tool_input.get("command", "")
    if not command_string:
        return None

    executed_command_text = command_text_the_shell_executes(command_string)
    triggered_streaming_rules = find_streaming_anti_patterns_in_command(
        command_text_outside_inert_heredoc_bodies(command_string)
    )
    triggered_hang_rules = find_hang_anti_patterns_in_command(executed_command_text)
    triggered_busy_wait_rules = find_busy_wait_anti_patterns_in_command(
        executed_command_text
    )
    if not (
        triggered_streaming_rules or triggered_hang_rules or triggered_busy_wait_rules
    ):
        return None

    return HandlerResult(
        decision="deny",
        reason=build_deny_reason_message(
            triggered_streaming_rules,
            triggered_hang_rules,
            triggered_busy_wait_rules,
            streamed_execution_context_label_for_tool(tool_name),
        ),
    )
