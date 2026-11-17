import itertools

import pytest
from merge_request_target_test_support import (
    BETHA_CHECKOUT,
    BETHA_GITLAB_HOST,
    guard,
    install_machine_the_guard_looks_at,
)

INVOCATION_PREFIXES = (
    "",
    f"GITLAB_HOST={BETHA_GITLAB_HOST} ",
    'GIT_SSH_COMMAND="ssh -4" ',
    f"env GITLAB_HOST={BETHA_GITLAB_HOST} ",
    "rtk ",
    "rtk proxy ",
    "/opt/homebrew/bin/",
    "timeout 120 ",
    f"cd {BETHA_CHECKOUT} && ",
    "git push -u origin feature && ",
)

COMMAND_LINE_CREATIONS = (
    "glab mr create --source-branch feature --target-branch main "
    '--title "feat: thing" --description "$(cat /tmp/body.md)"{assignee} --yes',
    "glab -R group/project mr new --fill{assignee}",
    "glab mr create{assignee} --fill --yes 2>&1 | tail -1",
)

COMMAND_LINE_ASSIGNEES = (
    " --assignee @me",
    " --assignee=someone",
    " -a @me",
    " -a=someone",
)

REST_CREATIONS = (
    "glab api -X POST projects/7/merge_requests -f source_branch=feature "
    '-f target_branch=main -f "title=feat: thing"{assignee}',
    "glab api projects/group%2Fproject/merge_requests "
    "-f source_branch=feature -f title=thing{assignee}",
    "glab api --method=post projects/:id/merge_requests --input /tmp/body.json{assignee}",
    'curl -sS -X POST -H "PRIVATE-TOKEN: $TOKEN" '
    f'"https://{BETHA_GITLAB_HOST}/api/v4/projects/7/merge_requests" '
    '--data "source_branch=feature"{assignee}',
    "curl -sS --request POST --data-binary @/tmp/body.json "
    f"https://{BETHA_GITLAB_HOST}/api/v4/projects/7/merge_requests/"
    "{assignee}",
)

REST_ASSIGNEES = (
    " -f assignee_id=42",
    ' -F "assignee_ids[]=42"',
    ' --data "assignee_id=$ME"',
)


@pytest.fixture(autouse=True)
def machine(monkeypatch):
    return install_machine_the_guard_looks_at(monkeypatch)


def commands_from(creations, assignees):
    return [
        prefix + creation.format(assignee=assignee)
        for prefix, creation, assignee in itertools.product(
            INVOCATION_PREFIXES, creations, assignees
        )
    ]


@pytest.mark.parametrize("command", commands_from(COMMAND_LINE_CREATIONS, ("",)))
def test_denies_every_command_line_creation_that_names_no_assignee(command):
    result = guard(command)
    assert result is not None, command
    assert result.decision == "deny"
    assert "--assignee @me" in result.reason


@pytest.mark.parametrize(
    "command", commands_from(COMMAND_LINE_CREATIONS, COMMAND_LINE_ASSIGNEES)
)
def test_allows_every_command_line_creation_that_names_an_assignee(command):
    assert guard(command) is None, command


@pytest.mark.parametrize("command", commands_from(REST_CREATIONS, ("",)))
def test_denies_every_rest_creation_that_names_no_assignee(command):
    result = guard(command)
    assert result is not None, command
    assert result.decision == "deny"
    assert "assignee_id" in result.reason


@pytest.mark.parametrize("command", commands_from(REST_CREATIONS, REST_ASSIGNEES))
def test_allows_every_rest_creation_that_names_an_assignee(command):
    assert guard(command) is None, command


def test_allows_a_rest_creation_naming_the_assignee_in_the_query_string():
    assert (
        guard(
            "curl -X POST --data-binary @/tmp/body.json "
            f'"https://{BETHA_GITLAB_HOST}/api/v4/projects/1/merge_requests'
            '?assignee_id=7"'
        )
        is None
    )


@pytest.mark.parametrize(
    "command",
    [
        'jq -n \'{source_branch:"feature", title:"thing", assignee_id:42}\' '
        '| glab api -X POST "projects/1/merge_requests" --input - '
        '-H "Content-Type: application/json"',
        "cat > /tmp/body.json <<'EOF'\n"
        '{"source_branch": "feature", "title": "thing", "assignee_ids": [42]}\n'
        "EOF\n"
        "glab api -X POST projects/1/merge_requests --input /tmp/body.json",
    ],
)
def test_allows_a_rest_creation_whose_body_is_built_with_an_assignee(command):
    assert guard(command) is None, command


def test_ignores_a_collection_path_quoted_inside_a_field_of_another_request():
    assert (
        guard(
            "glab api -X POST projects/1/issues "
            '-f "description=see https://gitlab.example.com/projects/1/merge_requests"'
        )
        is None
    )
