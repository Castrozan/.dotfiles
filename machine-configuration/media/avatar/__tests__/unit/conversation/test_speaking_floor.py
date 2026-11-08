import concurrent.futures
from unittest.mock import Mock

import conversation_addressee
import speaking_floor
import transcript_log
from conversation_addressee import Addressee
from wake_fakes import IBARAKI, VOYAGER
from wake_phrase import LiveSession


def floor(sessions=(VOYAGER, IBARAKI), listening=True):
    return speaking_floor.FloorBoundaries(
        sessions=Mock(return_value=list(sessions)),
        listening=Mock(return_value=listening),
    )


def said(directory, text, source="human", speaker=None):
    transcript_log.append(
        directory / speaking_floor.TRANSCRIPT_FILE, source, text, speaker
    )


def speaks(directory, session, boundaries=None):
    holder = speaking_floor.claim(directory, session.pane, boundaries or floor())
    return speaking_floor.may_speak(holder, session.pane)


def test_without_listening_anyone_may_speak_and_no_floor_is_kept(tmp_path):
    assert speaks(tmp_path, VOYAGER, floor(listening=False))
    assert speaks(tmp_path, IBARAKI, floor(listening=False))
    assert conversation_addressee.current(tmp_path) is None


def test_the_first_to_speak_holds_the_floor_and_the_second_stays_silent(tmp_path):
    said(tmp_path, "what does everyone think")
    assert speaks(tmp_path, VOYAGER)
    assert not speaks(tmp_path, IBARAKI)
    assert speaks(tmp_path, VOYAGER)


def test_naming_an_agent_hands_it_the_floor_without_a_greeting(tmp_path):
    said(tmp_path, "what does everyone think")
    speaks(tmp_path, VOYAGER)
    said(tmp_path, "Ibaraki, do you agree")
    assert not speaks(tmp_path, VOYAGER)
    assert speaks(tmp_path, IBARAKI)
    said(tmp_path, "and the tests")
    assert speaks(tmp_path, IBARAKI), "unnamed follow-ups stay with the holder"


def test_a_name_closing_the_line_also_hands_the_floor(tmp_path):
    speaks(tmp_path, VOYAGER)
    said(tmp_path, "what do you think, Ibaraki?")
    assert speaks(tmp_path, IBARAKI)


def test_the_latest_name_wins(tmp_path):
    said(tmp_path, "Ibaraki, start")
    said(tmp_path, "actually Voyager")
    assert speaks(tmp_path, VOYAGER)
    assert not speaks(tmp_path, IBARAKI)


def test_a_name_inside_a_sentence_is_not_an_address(tmp_path):
    speaks(tmp_path, VOYAGER)
    said(tmp_path, "I think Ibaraki broke the build")
    assert speaks(tmp_path, VOYAGER)


def test_the_avatar_echoing_a_name_moves_no_floor(tmp_path):
    speaks(tmp_path, VOYAGER)
    said(tmp_path, "Ibaraki, take it from here", speaker="avatar")
    assert speaks(tmp_path, VOYAGER)


def test_a_holder_whose_session_ended_loses_the_floor(tmp_path):
    speaks(tmp_path, VOYAGER)
    said(tmp_path, "anyone")
    assert speaks(tmp_path, IBARAKI, floor(sessions=(IBARAKI,)))


def test_a_session_without_a_servant_speaks_but_holds_nothing(tmp_path):
    stranger = LiveSession("unnamed", "wW:pXX")
    assert speaks(tmp_path, stranger)
    assert conversation_addressee.current(tmp_path) is None


def test_a_session_without_a_servant_cannot_talk_over_the_holder(tmp_path):
    speaks(tmp_path, VOYAGER)
    assert not speaks(tmp_path, LiveSession("unnamed", "wW:pXX"))


def test_the_holder_speaking_again_skips_the_fleet_lookup(tmp_path):
    conversation_addressee.hand_to(
        tmp_path, Addressee(VOYAGER.pane, VOYAGER.servant, 0)
    )
    boundaries = floor()
    assert speaks(tmp_path, VOYAGER, boundaries)
    boundaries.sessions.assert_not_called()


def test_a_wake_handover_and_a_claim_agree(tmp_path):
    said(tmp_path, "hey Ibaraki, status")
    conversation_addressee.hand_to(
        tmp_path, Addressee(IBARAKI.pane, IBARAKI.servant, 1)
    )
    assert not speaks(tmp_path, VOYAGER)
    assert speaks(tmp_path, IBARAKI)


def test_simultaneous_first_claims_grant_exactly_one_speaker(tmp_path):
    fleet = [LiveSession(f"Servant{index}", f"wW:p{index}") for index in range(8)]
    said(tmp_path, "anyone there")
    boundaries = floor(sessions=fleet)
    with concurrent.futures.ThreadPoolExecutor(len(fleet)) as pool:
        granted = list(
            pool.map(lambda session: speaks(tmp_path, session, boundaries), fleet)
        )
    assert granted.count(True) == 1
