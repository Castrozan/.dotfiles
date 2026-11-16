from __future__ import annotations

import os
import re
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

from hook_dispatch import HandlerResult  # noqa: E402

WITHOUT_ASSIGNEE_OVERRIDE_SENTINEL = "MERGE_REQUEST_WITHOUT_ASSIGNEE_SANCTIONED=1"
MERGE_REQUEST_ASSIGNEE_REFERENCE_FILE_PATH = "~/.claude/hooks/merge-request-assignee.md"
CREATION_VOCABULARY_PATTERN = re.compile(r"\bmr\b|\bpr\b|merge_requests")


def build_denial_reason(creation_form) -> str:
    return (
        f"BLOCKED (Bash): {creation_form.opened_request} with no assignee. "
        f"{creation_form.remedy} and run it again; read "
        f"{MERGE_REQUEST_ASSIGNEE_REFERENCE_FILE_PATH} for the other forms and "
        f"the override."
    )


def _creation_form_missing_an_assignee_in(command):
    from merge_request_creation_forms import creation_form_missing_an_assignee
    from shell_data_heredoc_bodies import shell_text_outside_data_heredoc_bodies
    from shell_simple_commands import (
        simple_commands_in,
        words_after_command_wrappers,
    )

    shell_text = shell_text_outside_data_heredoc_bodies(command)
    for simple_command_words in simple_commands_in(shell_text):
        creation_form = creation_form_missing_an_assignee(
            words_after_command_wrappers(simple_command_words), command
        )
        if creation_form is not None:
            return creation_form
    return None


def _bash_command_of(hook_input):
    if hook_input.get("tool_name", "") != "Bash":
        return ""
    return (hook_input.get("tool_input", {}) or {}).get("command", "") or ""


def _may_open_an_unassigned_request(command):
    return (
        bool(CREATION_VOCABULARY_PATTERN.search(command))
        and WITHOUT_ASSIGNEE_OVERRIDE_SENTINEL not in command
    )


def handle(hook_input):
    command = _bash_command_of(hook_input)
    if not _may_open_an_unassigned_request(command):
        return None
    creation_form = _creation_form_missing_an_assignee_in(command)
    if creation_form is None:
        return None
    reason = build_denial_reason(creation_form)
    return HandlerResult(decision="deny", reason=reason, system_message=reason)
