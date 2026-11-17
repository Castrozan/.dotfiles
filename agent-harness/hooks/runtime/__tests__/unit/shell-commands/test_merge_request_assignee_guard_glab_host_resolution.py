import pytest
from merge_request_target_test_support import (
    BETHA_CHECKOUT,
    BETHA_GITLAB_HOST,
    DIRECTORY_OUTSIDE_ANY_CHECKOUT,
    GITHUB_CHECKOUT,
    OTHER_GITLAB_CHECKOUT,
    assert_denied,
    guard,
    install_machine_the_guard_looks_at,
    merge_request_assignee_guard_handler,
)


@pytest.fixture(autouse=True)
def machine(monkeypatch):
    return install_machine_the_guard_looks_at(monkeypatch)


def test_a_repository_named_without_a_host_stays_on_the_checkout_host():
    command = "glab mr create --fill -R group/project"
    assert_denied(guard(command, BETHA_CHECKOUT), command)
    assert guard(command, OTHER_GITLAB_CHECKOUT) is None


def test_an_assignment_left_unexported_on_an_earlier_line_reaches_no_glab():
    command = f"GITLAB_HOST={BETHA_GITLAB_HOST}\nglab mr create --fill"
    assert guard(command, GITHUB_CHECKOUT) is None


def test_the_built_in_default_host_overrides_no_checkout():
    command = "GITLAB_HOST=gitlab.com glab mr create --fill --yes"
    assert_denied(guard(command, BETHA_CHECKOUT), command)
    assert guard(command, GITHUB_CHECKOUT) is None


@pytest.mark.parametrize("host_variable", ["GITLAB_HOST", "GL_HOST"])
def test_reads_the_host_from_the_environment_the_session_runs_in(
    monkeypatch, host_variable
):
    monkeypatch.setenv(host_variable, BETHA_GITLAB_HOST)
    assert_denied(guard("glab mr create --fill", GITHUB_CHECKOUT), host_variable)
    monkeypatch.setenv(host_variable, "gitlab.example.com")
    assert guard("glab mr create --fill", BETHA_CHECKOUT) is None


def test_a_host_named_on_the_command_wins_over_the_session_environment(monkeypatch):
    monkeypatch.setenv("GITLAB_HOST", BETHA_GITLAB_HOST)
    assert guard("GITLAB_HOST=gitlab.example.com glab mr create --fill") is None


def test_outside_any_checkout_the_glab_default_host_decides(machine):
    command = "glab api -X POST projects/7/merge_requests -f source_branch=feature"
    assert guard(command, DIRECTORY_OUTSIDE_ANY_CHECKOUT) is None
    machine.glab_default_host = BETHA_GITLAB_HOST
    assert_denied(guard(command, DIRECTORY_OUTSIDE_ANY_CHECKOUT), command)
    assert guard(command, OTHER_GITLAB_CHECKOUT) is None


def test_a_checkout_with_a_betha_remote_among_others_is_a_betha_target(machine):
    machine.remote_locations_by_directory[GITHUB_CHECKOUT] = {
        "git@github.com:owner/project.git",
        f"https://{BETHA_GITLAB_HOST}/group/project.git",
    }
    command = "glab mr create --fill --yes"
    assert_denied(guard(command, GITHUB_CHECKOUT), command)


def test_a_curl_call_follows_its_own_address_and_no_glab_setting(machine):
    machine.glab_default_host = BETHA_GITLAB_HOST
    command = (
        f"GITLAB_HOST={BETHA_GITLAB_HOST} curl -X POST -d source_branch=feature "
        "https://gitlab.example.com/api/v4/projects/7/merge_requests"
    )
    assert guard(command, BETHA_CHECKOUT) is None


def test_denies_the_betha_creation_that_follows_one_aimed_elsewhere():
    command = (
        "gh pr create --fill && "
        "glab mr create --fill -R https://gitlab.com/owner/project && "
        "glab mr create --fill --yes"
    )
    assert_denied(guard(command, BETHA_CHECKOUT), command)


def test_an_assigned_betha_creation_passes():
    assert guard("glab mr create --fill --yes --assignee @me", BETHA_CHECKOUT) is None


def test_a_session_without_a_working_directory_falls_back_to_the_process_one(
    machine, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    machine.remote_locations_by_directory[str(tmp_path.resolve())] = {
        f"git@{BETHA_GITLAB_HOST}:group/project.git"
    }
    result = merge_request_assignee_guard_handler.handle(
        {"tool_name": "Bash", "tool_input": {"command": "glab mr create --fill"}}
    )
    assert_denied(result, "no cwd in the hook input")
