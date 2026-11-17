from types import SimpleNamespace
from unittest.mock import Mock

import mac_stage
import pytest


@pytest.fixture
def stage(monkeypatch):
    state = SimpleNamespace(active=set(), ran=[], answers=True)
    monkeypatch.setattr(mac_stage.user_units, "unit_active", state.active.__contains__)
    monkeypatch.setattr(mac_stage.listener_session, "start_unit", state.active.add)
    monkeypatch.setattr(mac_stage.listener_session, "stop_unit", state.active.discard)
    monkeypatch.setattr(mac_stage, "answers", lambda port: state.answers)
    monkeypatch.setattr(mac_stage.local_window, "hide", Mock())
    monkeypatch.setattr(mac_stage.local_window, "show", Mock())
    monkeypatch.setattr(
        mac_stage.subprocess,
        "run",
        lambda command, **options: state.ran.append((command, options["timeout"])),
    )
    return state


def test_speech_on_a_bare_mac_raises_the_stage_and_strikes_it_after(stage):
    with mac_stage.standing():
        assert stage.active == set(mac_stage.STAGE_UNITS)
    assert stage.active == set()


def test_speech_in_a_conversation_leaves_its_stage_standing(stage):
    mac_stage.set_up()
    with mac_stage.standing():
        pass
    assert stage.active == set(mac_stage.STAGE_UNITS)


def test_a_control_server_that_never_answers_is_reported(stage, monkeypatch):
    stage.answers = False
    monkeypatch.setattr(mac_stage, "READY_WAIT_SECONDS", -1)
    with pytest.raises(TimeoutError, match="did not start"):
        mac_stage.set_up()


@pytest.mark.parametrize(
    ("voice", "tail"), [(None, ["speakers"]), ("a-voice", ["speakers", "a-voice"])]
)
def test_speech_goes_to_the_speakers_of_this_mac_in_the_chosen_voice(
    stage, voice, tail
):
    mac_stage.speak("Good evening", "happy", voice)
    command, timeout = stage.ran[0]
    assert command == ["avatar-command", "speak", "Good evening", "happy", *tail]
    assert timeout == mac_stage.SPEECH_TIMEOUT_SECONDS


def test_the_window_shows_the_renderer_of_this_mac(stage):
    mac_stage.show_window()
    mac_stage.local_window.show.assert_called_once_with(
        mac_stage.local_seat.RENDERER_PORT
    )
    assert stage.ran[0][0] == ["avatar-command", "presence", "shown"]


def test_no_character_asked_for_changes_nothing(stage):
    mac_stage.show_character(None)
    assert stage.ran == []
