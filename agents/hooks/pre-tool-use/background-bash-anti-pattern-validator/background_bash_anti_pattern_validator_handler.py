from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ANCESTOR_DIRECTORY = _MODULE_DIRECTORY
_SHARED_MODULE_CANDIDATE_DIRECTORIES = [_MODULE_DIRECTORY]
while _ANCESTOR_DIRECTORY != os.path.dirname(_ANCESTOR_DIRECTORY):
    _ANCESTOR_DIRECTORY = os.path.dirname(_ANCESTOR_DIRECTORY)
    _SHARED_MODULE_CANDIDATE_DIRECTORIES.append(
        os.path.join(_ANCESTOR_DIRECTORY, "common")
    )
for _shared_module_candidate_directory in _SHARED_MODULE_CANDIDATE_DIRECTORIES:
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

from background_bash_fake_success_detectors import (  # noqa: E402
    command_filters_by_hardcoded_long_literal_used_in_count_or_test,
    command_pipes_count_into_test_against_literal_zero,
    command_uses_until_loop_terminating_on_empty_count,
)
from background_daemon_spawner_detectors import (  # noqa: E402
    command_starts_a_lingering_daemon_or_service,
)
from foreground_ci_wait_detectors import (  # noqa: E402
    command_polls_ci_in_a_foreground_loop,
    command_waits_on_ci_in_the_foreground,
)
from hook_dispatch import HandlerResult  # noqa: E402
from interactive_command_hang_detectors import (  # noqa: E402
    command_launches_interactive_full_screen_program,
    command_runs_git_subcommand_that_opens_an_editor,
)
from shell_read_only_inspection_command import (  # noqa: E402
    command_text_the_shell_executes,
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


def build_lingering_daemon_deny_reason():
    return (
        "This background command starts a long-lived service, whose surviving "
        "children hold the task open past the command's own success. Run it "
        "detached with launch-command-detached-into-new-session <log> <command> "
        "and poll the log, or run it in the foreground. Read "
        f"{BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH}."
    )


def build_foreground_ci_wait_deny_reason():
    return (
        "Waiting on a CI run in the foreground parks this session for the whole "
        "run and streams its progress redraws into the context. Background it "
        "instead and the harness reports the exit, or poll 'gh run list' when a "
        f"verdict is actually due. See {BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH}."
    )


def build_foreground_ci_polling_loop_deny_reason():
    return (
        "This is a sleep-and-recheck loop over a CI run, which parks this session "
        "for every iteration it takes and buys nothing that one query at verdict "
        "time would not. Background the loop, or query once when the verdict is "
        f"actually due. See {BACKGROUND_BASH_PATTERNS_REFERENCE_FILE_PATH}."
    )


def handle(hook_input):
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    command_string = tool_input.get("command", "")
    if not command_string:
        return None

    executed_command_text = command_text_the_shell_executes(command_string)

    if not tool_input.get("run_in_background", False):
        if command_waits_on_ci_in_the_foreground(executed_command_text):
            return HandlerResult(
                decision="deny", reason=build_foreground_ci_wait_deny_reason()
            )
        if command_polls_ci_in_a_foreground_loop(executed_command_text):
            return HandlerResult(
                decision="deny", reason=build_foreground_ci_polling_loop_deny_reason()
            )
        return None

    triggered_rule_names = find_background_bash_anti_patterns_in_command(
        executed_command_text
    )
    if triggered_rule_names:
        return HandlerResult(
            decision="deny", reason=build_deny_reason_message(triggered_rule_names)
        )

    if command_starts_a_lingering_daemon_or_service(executed_command_text):
        deny_reason = build_lingering_daemon_deny_reason()
        return HandlerResult(decision="deny", reason=deny_reason)

    return None
