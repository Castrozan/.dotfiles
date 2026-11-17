from __future__ import annotations

import re

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


def flag_values(arguments, flags):
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
        *flag_values(arguments, REQUEST_METHOD_FLAGS),
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


def merge_request_collection_paths(arguments):
    return [
        request_path
        for request_path in _request_paths(arguments)
        if MERGE_REQUEST_COLLECTION_PATH_PATTERN.search(request_path)
    ]


def posts_to_merge_request_collection(arguments):
    return _request_method(arguments) == "POST" and bool(
        merge_request_collection_paths(arguments)
    )


def request_body_names_assignee(_arguments, whole_command_text):
    return bool(REST_ASSIGNEE_FIELD_PATTERN.search(whole_command_text))
