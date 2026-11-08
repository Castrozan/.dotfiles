import concurrent.futures
from unittest.mock import Mock

import conversation_addressee
import speaking_floor
from conversation_addressee import Addressee
from wake_fakes import IBARAKI, VOYAGER
from wake_phrase import LiveSession

STRANGER = LiveSession("unnamed", "wW:pXX")


def floor(sessions=(VOYAGER, IBARAKI), listening=True):
    return speaking_floor.FloorBoundaries(
        sessions=Mock(return_value=list(sessions)),
        listening=Mock(return_value=listening),
    )


def speaks(directory, session, boundaries=None):
    holder = speaking_floor.claim(directory, session.pane, boundaries or floor())
    return speaking_floor.may_speak(holder, session.pane)


def test_without_listening_anyone_may_speak_and_no_floor_is_kept(tmp_path):
    assert speaks(tmp_path, VOYAGER, floor(listening=False))
    assert speaks(tmp_path, IBARAKI, floor(listening=False))
    assert conversation_addressee.current(tmp_path) is None


def test_the_first_to_speak_holds_the_floor_and_the_second_stays_silent(tmp_path):
    assert speaks(tmp_path, VOYAGER)
    assert not speaks(tmp_path, IBARAKI)
    assert speaks(tmp_path, VOYAGER)


def test_the_session_the_wake_handed_the_floor_to_speaks_and_the_rest_wait(tmp_path):
    speaks(tmp_path, VOYAGER)
    conversation_addressee.hand_to(
        tmp_path, Addressee(IBARAKI.pane, IBARAKI.servant, 3)
    )
    assert not speaks(tmp_path, VOYAGER)
    assert speaks(tmp_path, IBARAKI)


def test_the_holder_speaking_again_reads_no_fleet(tmp_path):
    conversation_addressee.hand_to(
        tmp_path, Addressee(VOYAGER.pane, VOYAGER.servant, 0)
    )
    boundaries = floor()
    assert speaks(tmp_path, VOYAGER, boundaries)
    boundaries.sessions.assert_not_called()
    boundaries.listening.assert_not_called()


def test_a_holder_whose_session_ended_loses_the_floor_with_its_cursor(tmp_path):
    conversation_addressee.hand_to(
        tmp_path, Addressee(VOYAGER.pane, VOYAGER.servant, 5)
    )
    assert speaks(tmp_path, IBARAKI, floor(sessions=(IBARAKI,)))
    assert conversation_addressee.current(tmp_path) == Addressee(
        IBARAKI.pane, IBARAKI.servant, 5
    ), "the conversation's heard cursor survives the change of holder"


def test_a_session_without_a_servant_speaks_but_holds_nothing(tmp_path):
    assert speaks(tmp_path, STRANGER)
    assert conversation_addressee.current(tmp_path) is None


def test_a_session_without_a_servant_cannot_talk_over_the_holder(tmp_path):
    speaks(tmp_path, VOYAGER)
    assert not speaks(tmp_path, STRANGER)


def test_simultaneous_first_claims_grant_exactly_one_speaker(tmp_path):
    fleet = [LiveSession(f"Servant{index}", f"wW:p{index}") for index in range(8)]
    boundaries = floor(sessions=fleet)
    with concurrent.futures.ThreadPoolExecutor(len(fleet)) as pool:
        granted = list(
            pool.map(lambda session: speaks(tmp_path, session, boundaries), fleet)
        )
    assert granted.count(True) == 1
