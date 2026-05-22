#!/usr/bin/env python3

import json
import re
import sys

BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH = (
    "~/.claude/hooks/background-bash-anti-patterns.md"
)


def command_uses_until_loop_terminating_on_empty_count(command_string):
    return bool(
        re.search(
            r"until\b[\s\S]*?\[\s*\"?\$\([\s\S]+?\)\"?\s*=\s*\"?0\"?\s*\][\s\S]*?\bsleep\b",
            command_string,
        )
    )


def command_filters_by_hardcoded_long_literal_used_in_count_or_test(command_string):
    has_jq_select_with_long_literal = bool(
        re.search(
            r"select\s*\(\s*\.[A-Za-z_][\w.]*\s*==\s*\"[A-Za-z0-9_./-]{8,}\"\s*\)",
            command_string,
        )
    )
    has_downstream_count_or_zero_test = bool(
        re.search(r"\blength\b|\bwc\s+-l\b|=\s*\"?0\"?", command_string)
    )
    return has_jq_select_with_long_literal and has_downstream_count_or_zero_test


def command_pipes_count_into_test_against_literal_zero(command_string):
    return bool(
        re.search(
            r"\[\s*\"?\$\([^)]*\b(?:length|wc\s+-l)\b[^)]*\)\"?\s*=\s*\"?0\"?\s*\]",
            command_string,
        )
    )


PATTERN_DETECTORS_BY_RULE_NAME = {
    "until-loop-terminating-on-empty-count": command_uses_until_loop_terminating_on_empty_count,
    "jq-select-filter-with-hardcoded-literal-in-flow-control": command_filters_by_hardcoded_long_literal_used_in_count_or_test,
    "count-piped-into-test-against-zero": command_pipes_count_into_test_against_literal_zero,
}


def find_background_bash_anti_patterns_in_command(command_string):
    return [
        rule_name
        for rule_name, detector in PATTERN_DETECTORS_BY_RULE_NAME.items()
        if detector(command_string)
    ]


def build_deny_reason_message(triggered_rule_names):
    rules_list_text = ", ".join(triggered_rule_names)
    return (
        f"Background bash command matches anti-pattern(s): {rules_list_text}. "
        f"These shapes can exit 0 with empty output when a filter is wrong "
        f"(typo, fabricated literal, unset variable), indistinguishable from "
        f"genuine completion. "
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
