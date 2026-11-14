import itertools
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock

import conversation_addressee
import pytest
import room_holder
import servant_character
from conversation_addressee import Addressee
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

CHARACTERS = (
    "Scheherazade | vivi\nSasaki Kojirou | hair-sample-male\nCirce | darkness-shibu\n"
)


@pytest.fixture
def switches(monkeypatch, tmp_path):
    characters = tmp_path / "characters.txt"
    characters.write_text(CHARACTERS)
    monkeypatch.setenv(
        servant_character.CHARACTERS_ENVIRONMENT_VARIABLE, str(characters)
    )
    runner = Mock()
    monkeypatch.setattr(servant_character.subprocess, "run", runner)
    return runner


def switched_to(runner):
    return [call.args[0][2] for call in runner.call_args_list]


def test_the_first_holder_switches_the_character_once(switches, tmp_path):
    room_holder.give_the_room_to(tmp_path, Addressee("w:p1", "Scheherazade", 0))
    assert switched_to(switches) == ["vivi"]
    assert conversation_addressee.current(tmp_path).servant == "Scheherazade"


def test_a_changed_holder_switches_to_the_new_character(switches, tmp_path):
    room_holder.give_the_room_to(tmp_path, Addressee("w:p1", "Scheherazade", 0))
    room_holder.give_the_room_to(tmp_path, Addressee("w:p2", "Sasaki Kojirou", 0))
    assert switched_to(switches) == ["vivi", "hair-sample-male"]


def test_the_same_holder_twice_switches_nothing_more(switches, tmp_path):
    room_holder.give_the_room_to(tmp_path, Addressee("w:p1", "Scheherazade", 0))
    room_holder.give_the_room_to(tmp_path, Addressee("w:p1", "Scheherazade", 4))
    assert switched_to(switches) == ["vivi"]
    assert conversation_addressee.current(tmp_path).heard_through == 4


def test_the_same_servant_in_another_pane_switches_nothing(switches, tmp_path):
    room_holder.give_the_room_to(tmp_path, Addressee("w:p1", "Circe", 0))
    room_holder.give_the_room_to(tmp_path, Addressee("w:p2", "Circe", 0))
    assert switched_to(switches) == ["darkness-shibu"]


def test_a_failing_switch_raises_nothing_and_the_room_is_still_given(
    monkeypatch, switches, tmp_path
):
    switches.side_effect = subprocess.CalledProcessError(1, "avatar-command")
    room_holder.give_the_room_to(tmp_path, Addressee("w:p1", "Circe", 0))
    assert conversation_addressee.current(tmp_path).servant == "Circe"


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    handovers=st.lists(
        st.tuples(
            st.sampled_from(["w:p1", "w:p2", "w:p3"]),
            st.sampled_from(["Scheherazade", "Sasaki Kojirou", "Circe", "Unlisted"]),
        )
    )
)
def test_the_character_switches_exactly_when_the_servant_changes(switches, handovers):
    switches.reset_mock()
    characters = {
        "Scheherazade": "vivi",
        "Sasaki Kojirou": "hair-sample-male",
        "Circe": "darkness-shibu",
    }
    with tempfile.TemporaryDirectory() as directory:
        for pane, servant in handovers:
            room_holder.give_the_room_to(Path(directory), Addressee(pane, servant, 0))
    changes = [servant for servant, _ in itertools.groupby(s for _, s in handovers)]
    assert switched_to(switches) == [
        characters[servant] for servant in changes if servant in characters
    ]
