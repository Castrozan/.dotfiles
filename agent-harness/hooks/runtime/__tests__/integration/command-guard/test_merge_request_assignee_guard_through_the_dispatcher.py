import json
import subprocess

import pytest
from hook_module_loader import find_hook_module_path, run_hook_subprocess

PRE_TOOL_USE_DISPATCHER = find_hook_module_path("pre-tool-use-dispatcher")
BETHA_GITLAB_HOST = "gitlab.services.betha.cloud"
GLAB_HOST_VARIABLES = ("GITLAB_HOST", "GL_HOST")
UNASSIGNED_REST_CREATION = (
    "glab api -X POST projects/1/merge_requests -f source_branch=feature"
)


@pytest.fixture(autouse=True)
def glab_settings_of_no_machine(monkeypatch, tmp_path):
    for host_variable in GLAB_HOST_VARIABLES:
        monkeypatch.delenv(host_variable, raising=False)
    empty_glab_configuration = tmp_path / "glab-configuration"
    empty_glab_configuration.mkdir()
    monkeypatch.setenv("GLAB_CONFIG_DIR", str(empty_glab_configuration))


def checkout_whose_origin_is(tmp_path, origin_location):
    checkout = tmp_path / "checkout"
    subprocess.run(["git", "init", "--quiet", str(checkout)], check=True)
    subprocess.run(
        ["git", "-C", str(checkout), "remote", "add", "origin", origin_location],
        check=True,
    )
    return str(checkout)


@pytest.fixture
def betha_checkout(tmp_path):
    return checkout_whose_origin_is(
        tmp_path, f"https://{BETHA_GITLAB_HOST}/group/project.git"
    )


@pytest.fixture
def github_checkout(tmp_path):
    return checkout_whose_origin_is(tmp_path, "https://github.com/owner/project.git")


@pytest.fixture
def other_gitlab_checkout(tmp_path):
    return checkout_whose_origin_is(tmp_path, "https://gitlab.com/owner/project.git")


def dispatched_permission_decision(command, working_directory):
    payload = {
        "session_id": "merge-request-assignee-guard",
        "transcript_path": "/dev/null",
        "cwd": working_directory,
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    completed = run_hook_subprocess(PRE_TOOL_USE_DISPATCHER, json.dumps(payload))
    assert completed.returncode == 0, completed.stderr
    if not completed.stdout.strip():
        return {}
    return json.loads(completed.stdout).get("hookSpecificOutput", {})


@pytest.mark.parametrize(
    "command, remedy",
    [
        ("glab mr create --fill --yes", "--assignee @me"),
        ("rtk glab mr new --fill -R group/project", "--assignee @me"),
        (UNASSIGNED_REST_CREATION, "assignee_id"),
    ],
)
def test_the_dispatcher_denies_an_unassigned_creation_in_a_betha_checkout(
    betha_checkout, command, remedy
):
    decision = dispatched_permission_decision(command, betha_checkout)
    assert decision.get("permissionDecision") == "deny", command
    assert remedy in decision.get("permissionDecisionReason", "")


@pytest.mark.parametrize(
    "command",
    [
        "glab mr create --fill --yes --assignee @me",
        f"{UNASSIGNED_REST_CREATION} -f assignee_id=42",
        "gh pr create --fill",
        "git push -u origin feature -o merge_request.create",
        "glab mr list",
        "GITLAB_HOST=gitlab.example.com glab mr create --fill --yes",
        "glab mr create --fill -R https://gitlab.com/owner/project",
    ],
)
def test_the_dispatcher_lets_the_rest_through_in_a_betha_checkout(
    betha_checkout, command
):
    decision = dispatched_permission_decision(command, betha_checkout)
    assert decision.get("permissionDecision") != "deny", decision


@pytest.mark.parametrize(
    "command", ["glab mr create --fill --yes", UNASSIGNED_REST_CREATION]
)
def test_the_dispatcher_lets_an_unassigned_creation_through_outside_betha(
    request, tmp_path, command
):
    directories_that_are_not_betha = [
        request.getfixturevalue("other_gitlab_checkout"),
        str(tmp_path),
        str(tmp_path / "removed"),
    ]
    for working_directory in directories_that_are_not_betha:
        decision = dispatched_permission_decision(command, working_directory)
        assert decision.get("permissionDecision") != "deny", working_directory


def test_the_dispatcher_lets_a_github_pull_request_through(github_checkout):
    for command in ("gh pr create --fill", "glab mr create --fill --yes"):
        decision = dispatched_permission_decision(command, github_checkout)
        assert decision.get("permissionDecision") != "deny", command


@pytest.mark.parametrize(
    "command",
    [
        f"GITLAB_HOST={BETHA_GITLAB_HOST} rtk glab mr create --fill",
        f"glab mr create --fill -R https://{BETHA_GITLAB_HOST}/group/project",
        f"glab api --hostname {BETHA_GITLAB_HOST} -X POST projects/1/merge_requests "
        "-f source_branch=feature",
        f"curl -X POST -d source_branch=feature "
        f"https://{BETHA_GITLAB_HOST}/api/v4/projects/1/merge_requests",
    ],
)
def test_the_dispatcher_denies_a_creation_that_names_betha_from_a_github_checkout(
    github_checkout, command
):
    decision = dispatched_permission_decision(command, github_checkout)
    assert decision.get("permissionDecision") == "deny", command


def test_the_dispatcher_follows_a_directory_change_into_a_betha_checkout(
    betha_checkout, tmp_path
):
    decision = dispatched_permission_decision(
        f"cd {betha_checkout} && glab mr create --fill --yes", str(tmp_path)
    )
    assert decision.get("permissionDecision") == "deny"
