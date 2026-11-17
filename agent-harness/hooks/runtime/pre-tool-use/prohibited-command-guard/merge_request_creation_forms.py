from __future__ import annotations

from merge_request_rest_calls import (
    flag_values,
    merge_request_collection_paths,
    posts_to_merge_request_collection,
    request_body_names_assignee,
)

CREATING_SUBCOMMANDS = frozenset({"create", "new"})
HELP_FLAGS = frozenset({"--help", "-h"})
REPOSITORY_FLAGS = frozenset({"-R", "--repo"})
HOSTNAME_FLAGS = frozenset({"--hostname"})
OPENED_BY_A_REST_CALL = "this POST to merge_requests opens a merge request"
REST_CALL_REMEDY = "Send `assignee_id=<your user id>` in the same command"


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


def _glab_creates_merge_request(invocation_words):
    return _command_name(invocation_words) == "glab" and _runs_creating_subcommand(
        invocation_words[1:], "mr"
    )


def _glab_api_call_creates_merge_request(invocation_words):
    arguments = invocation_words[1:]
    return (
        _command_name(invocation_words) == "glab"
        and "api" in arguments
        and posts_to_merge_request_collection(arguments)
    )


def _curl_call_creates_merge_request(invocation_words):
    return _command_name(
        invocation_words
    ) == "curl" and posts_to_merge_request_collection(invocation_words[1:])


def _first_of(candidates):
    return next(iter(candidates), "")


def _location_named_by_the_repository_flag(arguments):
    return _first_of(
        repository
        for repository in flag_values(arguments, REPOSITORY_FLAGS)
        if ":" in repository
    )


def _location_named_by_a_glab_api_call(arguments):
    request_addresses = [
        request_path
        for request_path in merge_request_collection_paths(arguments)
        if "://" in request_path
    ]
    return _first_of([*flag_values(arguments, HOSTNAME_FLAGS), *request_addresses])


def _location_named_by_a_curl_call(arguments):
    return _first_of(merge_request_collection_paths(arguments))


class MergeRequestCreationForm:
    def __init__(
        self,
        opened_request,
        creates,
        names_an_assignee,
        location_named_by,
        resolves_its_host_as_glab_does,
        remedy,
    ):
        self.opened_request = opened_request
        self.creates = creates
        self.names_an_assignee = names_an_assignee
        self.location_named_by = location_named_by
        self.resolves_its_host_as_glab_does = resolves_its_host_as_glab_does
        self.remedy = remedy


MERGE_REQUEST_CREATION_FORMS = (
    MergeRequestCreationForm(
        opened_request="'glab mr create' opens a merge request",
        creates=_glab_creates_merge_request,
        names_an_assignee=_carries_assignee_flag,
        location_named_by=_location_named_by_the_repository_flag,
        resolves_its_host_as_glab_does=True,
        remedy="Add `--assignee @me`",
    ),
    MergeRequestCreationForm(
        opened_request=OPENED_BY_A_REST_CALL,
        creates=_glab_api_call_creates_merge_request,
        names_an_assignee=request_body_names_assignee,
        location_named_by=_location_named_by_a_glab_api_call,
        resolves_its_host_as_glab_does=True,
        remedy=REST_CALL_REMEDY,
    ),
    MergeRequestCreationForm(
        opened_request=OPENED_BY_A_REST_CALL,
        creates=_curl_call_creates_merge_request,
        names_an_assignee=request_body_names_assignee,
        location_named_by=_location_named_by_a_curl_call,
        resolves_its_host_as_glab_does=False,
        remedy=REST_CALL_REMEDY,
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
