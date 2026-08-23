import pytest

import interactive_session_detection


@pytest.fixture
def clawde_agent_workspaces(tmp_path, monkeypatch):
    agent_workspaces_directory = tmp_path / "clawde"
    (agent_workspaces_directory / "monster").mkdir(parents=True)
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", str(agent_workspaces_directory))
    return agent_workspaces_directory


def test_shared_interactive_preferences_mark_the_session_as_keyboard_driven(
    monkeypatch,
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH",
        "/nix/store/interactive-session-only-instructions.md",
    )

    assert interactive_session_detection.is_keyboard_driven_interactive_session()


def test_an_agent_workspace_is_a_background_agent_session_without_the_launcher_marker(
    clawde_agent_workspaces, monkeypatch
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.chdir(clawde_agent_workspaces / "monster")

    assert interactive_session_detection.is_clawde_background_agent_session()


def test_an_agent_workspace_turn_is_never_keyboard_driven(
    clawde_agent_workspaces, monkeypatch
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH",
        "/nix/store/interactive-session-only-instructions.md",
    )
    monkeypatch.chdir(clawde_agent_workspaces / "monster")

    assert not interactive_session_detection.is_keyboard_driven_interactive_session()


def test_a_directory_outside_the_agent_workspaces_stays_a_human_session(
    clawde_agent_workspaces, monkeypatch, tmp_path
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.chdir(tmp_path)

    assert not interactive_session_detection.is_clawde_background_agent_session()
