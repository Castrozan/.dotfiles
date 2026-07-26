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

from background_bash_fake_success_detectors import (  # noqa: E402
    command_filters_by_hardcoded_long_literal_used_in_count_or_test,
    command_pipes_count_into_test_against_literal_zero,
    command_uses_until_loop_terminating_on_empty_count,
)
from background_daemon_spawner_detectors import (  # noqa: E402
    command_starts_a_lingering_daemon_or_service,
)
from hook_dispatch import HandlerResult  # noqa: E402
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


def build_lingering_daemon_advisory_message():
    return (
        "This background command starts a long-lived service or daemon. The "
        "background task completes only when the whole process group exits, so a "
        "child left running in the same session makes the task hang even after "
        "the command itself succeeds (e.g. rebuild finishes but a restarted "
        "service keeps the group alive). Prefer: "
        "launch-command-detached-into-new-session <log_file> <command>, then poll "
        "<log_file> for the command's own success marker instead of waiting for "
        f"the completion notification. See {BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH}."
    )


def handle(hook_input):
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    if not tool_input.get("run_in_background", False):
        return None

    command_string = tool_input.get("command", "")
    if not command_string:
        return None

    triggered_rule_names = find_background_bash_anti_patterns_in_command(command_string)
    if triggered_rule_names:
        return HandlerResult(
            decision="deny", reason=build_deny_reason_message(triggered_rule_names)
        )

    if command_starts_a_lingering_daemon_or_service(command_string):
        advisory_message = build_lingering_daemon_advisory_message()
        return HandlerResult(
            additional_context=advisory_message, system_message=advisory_message
        )

    return None
