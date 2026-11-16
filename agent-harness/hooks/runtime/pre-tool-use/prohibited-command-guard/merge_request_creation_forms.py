from __future__ import annotations

import re

CREATING_SUBCOMMANDS = frozenset({"create", "new"})
HELP_FLAGS = frozenset({"--help", "-h"})
SHORT_REQUEST_METHOD_FLAG = "-X"
REQUEST_METHOD_FLAGS = frozenset({SHORT_REQUEST_METHOD_FLAG, "--method", "--request"})
QUERY_STRING_BODY_FLAGS = frozenset({"-G", "--get"})
REQUEST_BODY_FLAGS = frozenset(
    "-f --raw-field -F --field --form --input -d --data --data-raw --data-binary "
    "--data-urlencode --json".split()
)
MERGE_REQUEST_COLLECTION_PATH_PATTERN = re.compile(
    r"(?:^|/)projects/[^/\s]+/merge_requests/?$"
)
REST_ASSIGNEE_FIELD_PATTERN = re.compile(r"assignee_ids?(?:\[\])?[\"']?\s*[:=]")
REST_CLIENT_COMMAND_NAMES = frozenset({"glab", "curl"})


def _command_name(invocation_words):
    return invocation_words[0].rsplit("/", 1)[-1]


def _runs_creating_subcommand(arguments, resource):
    if HELP_FLAGS.intersection(arguments):
        return False
    return any(
        argument == resource and following_argument in CREATING_SUBCOMMANDS
        for argument, following_argument in zip(arguments, arguments[1:], strict=False)
    )


def _carries_assignee_flag(arguments, _whole_command_text):
    return any(
        argument == "--assignee"
        or argument.startswith("--assignee=")
        or (argument.startswith("-a") and not argument.startswith("--"))
        for argument in arguments
    )


def _flag_values(arguments, flags):
    following_arguments = [*arguments[1:], ""]
    for argument, following_argument in zip(
        arguments, following_arguments, strict=True
    ):
        flag, joining_separator, joined_value = argument.partition("=")
        if flag in flags:
            yield joined_value if joining_separator else following_argument


def _methods_joined_to_the_short_flag(arguments):
    return [
        argument[len(SHORT_REQUEST_METHOD_FLAG) :]
        for argument in arguments
        if argument.startswith(SHORT_REQUEST_METHOD_FLAG)
        and argument != SHORT_REQUEST_METHOD_FLAG
    ]


def _sends_a_body(arguments):
    return any(
        argument.partition("=")[0] in REQUEST_BODY_FLAGS for argument in arguments
    )


def _request_method(arguments):
    if QUERY_STRING_BODY_FLAGS.intersection(arguments):
        return "GET"
    explicit_methods = [
        *_flag_values(arguments, REQUEST_METHOD_FLAGS),
        *_methods_joined_to_the_short_flag(arguments),
    ]
    if explicit_methods:
        return explicit_methods[0].upper()
    return "POST" if _sends_a_body(arguments) else "GET"


def _request_paths(arguments):
    for argument in arguments:
        request_path = argument.partition("?")[0]
        if "=" not in request_path:
            yield request_path


def _posts_to_merge_request_collection(arguments):
    if _request_method(arguments) != "POST":
        return False
    return any(
        MERGE_REQUEST_COLLECTION_PATH_PATTERN.search(request_path)
        for request_path in _request_paths(arguments)
    )


def _request_body_names_assignee(_arguments, whole_command_text):
    return bool(REST_ASSIGNEE_FIELD_PATTERN.search(whole_command_text))


def _glab_creates_merge_request(invocation_words):
    return _command_name(invocation_words) == "glab" and _runs_creating_subcommand(
        invocation_words[1:], "mr"
    )


def _gh_creates_pull_request(invocation_words):
    return _command_name(invocation_words) == "gh" and _runs_creating_subcommand(
        invocation_words[1:], "pr"
    )


def _rest_call_creates_merge_request(invocation_words):
    command_name = _command_name(invocation_words)
    arguments = invocation_words[1:]
    if command_name not in REST_CLIENT_COMMAND_NAMES:
        return False
    if command_name == "glab" and "api" not in arguments:
        return False
    return _posts_to_merge_request_collection(arguments)


class MergeRequestCreationForm:
    def __init__(self, opened_request, creates, names_an_assignee, remedy):
        self.opened_request = opened_request
        self.creates = creates
        self.names_an_assignee = names_an_assignee
        self.remedy = remedy


MERGE_REQUEST_CREATION_FORMS = (
    MergeRequestCreationForm(
        opened_request="'glab mr create' opens a merge request",
        creates=_glab_creates_merge_request,
        names_an_assignee=_carries_assignee_flag,
        remedy="Add `--assignee @me`",
    ),
    MergeRequestCreationForm(
        opened_request="'gh pr create' opens a pull request",
        creates=_gh_creates_pull_request,
        names_an_assignee=_carries_assignee_flag,
        remedy="Add `--assignee @me`",
    ),
    MergeRequestCreationForm(
        opened_request="this POST to merge_requests opens a merge request",
        creates=_rest_call_creates_merge_request,
        names_an_assignee=_request_body_names_assignee,
        remedy="Send `assignee_id=<your user id>` in the same command",
    ),
)


def creation_form_missing_an_assignee(invocation_words, whole_command_text):
    if not invocation_words:
        return None
    for creation_form in MERGE_REQUEST_CREATION_FORMS:
        if not creation_form.creates(invocation_words):
            continue
        if creation_form.names_an_assignee(invocation_words[1:], whole_command_text):
            return None
        return creation_form
    return None
