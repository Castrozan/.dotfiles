import pytest

from clawde_workspace_paths import agents_directory


@pytest.fixture
def home_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWDE_AGENTS_DIRECTORY", raising=False)
    return tmp_path


def test_the_default_root_is_clawde_under_the_home_directory(home_directory):
    assert agents_directory() == (home_directory / "clawde").resolve()


def test_a_configured_root_wins_over_the_default(home_directory, monkeypatch):
    configured = home_directory / "elsewhere" / "agents"
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", str(configured))

    assert agents_directory() == configured.resolve()


def test_a_configured_root_expands_the_home_shorthand(home_directory, monkeypatch):
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", "~/agents")

    assert agents_directory() == (home_directory / "agents").resolve()


def test_a_configured_root_resolves_relative_steps_away(home_directory, monkeypatch):
    monkeypatch.setenv(
        "CLAWDE_AGENTS_DIRECTORY", str(home_directory / "nested" / ".." / "agents")
    )

    assert agents_directory() == (home_directory / "agents").resolve()


def test_an_empty_configured_root_falls_back_to_the_default(
    home_directory, monkeypatch
):
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", "")

    assert agents_directory() == (home_directory / "clawde").resolve()
