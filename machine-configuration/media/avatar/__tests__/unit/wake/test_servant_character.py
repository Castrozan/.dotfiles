import pathlib
import subprocess
import tempfile
from unittest.mock import Mock

import pytest
import servant_character
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


@pytest.fixture
def characters_file(monkeypatch, tmp_path):
    path = tmp_path / "characters.txt"
    path.write_text("Medea | victoria-rubin\nYan Qing | sakurada-fumiriya\n")
    monkeypatch.setenv(servant_character.CHARACTERS_ENVIRONMENT_VARIABLE, str(path))
    return path


def test_a_listed_servant_has_its_character(characters_file):
    assert servant_character.character_for("Medea") == "victoria-rubin"
    assert servant_character.character_for("Yan Qing") == "sakurada-fumiriya"


def test_an_unknown_servant_has_no_character(characters_file):
    assert servant_character.character_for("Merlin") is None


def test_a_name_that_only_starts_like_a_listed_one_has_no_character(characters_file):
    assert servant_character.character_for("Yan") is None


def test_without_the_environment_variable_there_is_no_character(monkeypatch):
    monkeypatch.delenv(servant_character.CHARACTERS_ENVIRONMENT_VARIABLE, raising=False)
    assert servant_character.character_for("Medea") is None


def test_a_missing_file_gives_no_character(monkeypatch, tmp_path):
    monkeypatch.setenv(
        servant_character.CHARACTERS_ENVIRONMENT_VARIABLE, str(tmp_path / "absent.txt")
    )
    assert servant_character.character_for("Medea") is None


def test_showing_runs_the_switch_with_a_timeout(monkeypatch, characters_file):
    runner = Mock()
    monkeypatch.setattr(servant_character.subprocess, "run", runner)
    servant_character.show_for("Medea")
    assert runner.call_args.args[0] == ["avatar-command", "character", "victoria-rubin"]
    assert (
        runner.call_args.kwargs["timeout"] == servant_character.SWITCH_TIMEOUT_SECONDS
    )


def test_showing_a_servant_without_a_character_runs_nothing(
    monkeypatch, characters_file
):
    runner = Mock()
    monkeypatch.setattr(servant_character.subprocess, "run", runner)
    servant_character.show_for("Merlin")
    runner.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.CalledProcessError(1, "avatar-command"),
        subprocess.TimeoutExpired("avatar-command", 30),
        FileNotFoundError("avatar-command"),
    ],
)
def test_a_failing_switch_raises_nothing(monkeypatch, characters_file, failure):
    monkeypatch.setattr(servant_character.subprocess, "run", Mock(side_effect=failure))
    servant_character.show_for("Medea")


LISTED_NAMES = st.text(alphabet="abcdefg ()'", min_size=1, max_size=8).filter(
    lambda name: name == name.strip()
)
CHARACTER_NAMES = st.text(alphabet="abcdefg-", min_size=1, max_size=8)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    listed=st.dictionaries(LISTED_NAMES, CHARACTER_NAMES, max_size=6),
    asked=LISTED_NAMES,
)
def test_a_servant_has_exactly_the_character_its_line_names(monkeypatch, listed, asked):
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "characters.txt"
        path.write_text(
            "".join(f"{name} | {character}\n" for name, character in listed.items())
        )
        monkeypatch.setenv(servant_character.CHARACTERS_ENVIRONMENT_VARIABLE, str(path))
        assert servant_character.character_for(asked) == listed.get(asked)
