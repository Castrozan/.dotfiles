#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from background_bash_fake_success_detectors import (  # noqa: E402
    command_filters_by_hardcoded_long_literal_used_in_count_or_test,
    command_pipes_count_into_test_against_literal_zero,
    command_uses_until_loop_terminating_on_empty_count,
)
from interactive_command_hang_detectors import (  # noqa: E402
    command_launches_interactive_full_screen_program,
    command_runs_git_subcommand_that_opens_an_editor,
)

BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH = (
    "~/.claude/hooks/background-bash-anti-patterns.md"
)

PATTERN_DETECTORS_BY_RULE_NAME = {
    "until-loop-terminating-on-empty-count": command_uses_until_loop_terminating_on_empty_count,
    "jq-select-filter-with-hardcoded-literal-in-flow-control": command_filters_by_hardcoded_long_literal_used_in_count_or_test,
    "count-piped-into-test-against-zero": command_pipes_count_into_test_against_literal_zero,
    "interactive-editor-or-full-screen-tui": command_launches_interactive_full_screen_program,
    "git-subcommand-that-opens-an-editor": command_runs_git_subcommand_that_opens_an_editor,
}

FAILURE_MODE_BY_RULE_NAME = {
    "until-loop-terminating-on-empty-count": "silent-fake-success",
    "jq-select-filter-with-hardcoded-literal-in-flow-control": "silent-fake-success",
    "count-piped-into-test-against-zero": "silent-fake-success",
    "interactive-editor-or-full-screen-tui": "hang-forever",
    "git-subcommand-that-opens-an-editor": "hang-forever",
}

FAILURE_MODE_EXPLANATIONS = {
    "silent-fake-success": (
        "can exit 0 with empty output when a filter is wrong (typo, fabricated "
        "literal, unset variable), indistinguishable from genuine completion"
    ),
    "hang-forever": (
        "block forever on a controlling terminal that a background task does not "
        "have (interactive editor, full-screen TUI, or a git subcommand that opens "
        "an editor), so the command never exits and the completion notification "
        "never arrives"
    ),
}


def find_background_bash_anti_patterns_in_command(command_string):
    return [
        rule_name
        for rule_name, detector in PATTERN_DETECTORS_BY_RULE_NAME.items()
        if detector(command_string)
    ]


def build_deny_reason_message(triggered_rule_names):
    rules_list_text = ", ".join(triggered_rule_names)
    failure_modes_in_first_seen_order = []
    for rule_name in triggered_rule_names:
        failure_mode = FAILURE_MODE_BY_RULE_NAME[rule_name]
        if failure_mode not in failure_modes_in_first_seen_order:
            failure_modes_in_first_seen_order.append(failure_mode)
    failure_mode_explanation_text = "; ".join(
        FAILURE_MODE_EXPLANATIONS[failure_mode]
        for failure_mode in failure_modes_in_first_seen_order
    )
    return (
        f"Background bash command matches anti-pattern(s): {rules_list_text}. "
        f"These shapes {failure_mode_explanation_text}. "
        f"Read {BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH} for the correct "
        f"invocation patterns, then retry."
    )


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

    if hook_input.get("tool_name") != "Bash":
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    is_run_in_background = tool_input.get("run_in_background", False)
    if not is_run_in_background:
        sys.exit(0)

    command_string = tool_input.get("command", "")
    if not command_string:
        sys.exit(0)

    triggered_rule_names = find_background_bash_anti_patterns_in_command(command_string)
    if not triggered_rule_names:
        sys.exit(0)

    emit_deny_decision_for_pre_tool_use_hook(
        build_deny_reason_message(triggered_rule_names)
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
