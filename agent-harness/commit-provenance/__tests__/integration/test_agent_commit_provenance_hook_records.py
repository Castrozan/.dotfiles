import pytest
from agent_commit_provenance_hook_test_support import (
    AMENDED_SESSION_IDENTIFIER,
    RECORDED_SESSION_IDENTIFIER,
    agent_session_environment,
    commit_a_change,
    latest_commit_message,
    latest_trailer_value,
    repository_with_the_hook_installed,
    run_git,
)


@pytest.fixture
def repository(tmp_path):
    return repository_with_the_hook_installed(tmp_path)


def test_a_commit_made_inside_an_agent_session_carries_its_resume_command(repository):
    commit_a_change(repository, "a.txt", "feat: first")
    assert latest_commit_message(repository) == (
        "feat: first\n"
        "\n"
        "Agent-Harness: claude\n"
        "Agent-Machine: testmachine\n"
        f"Agent-Session: {RECORDED_SESSION_IDENTIFIER}\n"
        f"Agent-Resume: claude --resume {RECORDED_SESSION_IDENTIFIER}"
    )


def test_a_fleet_agent_records_its_name(repository):
    commit_a_change(
        repository,
        "a.txt",
        "feat: fleet",
        environment=agent_session_environment()
        | {"CLAWDE_AGENT_NAME": "dotfiles-steward"},
    )
    assert latest_trailer_value(repository, "Agent-Name") == "dotfiles-steward"


def test_amending_replaces_the_trailers_instead_of_stacking_them(repository):
    commit_a_change(repository, "a.txt", "feat: first")
    run_git(
        repository,
        "commit",
        "--amend",
        "--no-edit",
        environment=agent_session_environment(AMENDED_SESSION_IDENTIFIER),
    )
    assert (
        latest_trailer_value(repository, "Agent-Session") == AMENDED_SESSION_IDENTIFIER
    )
    assert latest_commit_message(repository).count("Agent-Session:") == 1


def test_a_repository_can_opt_out(repository):
    run_git(repository, "config", "agent.provenance.enabled", "false")
    commit_a_change(repository, "a.txt", "feat: quiet")
    assert latest_commit_message(repository) == "feat: quiet"
