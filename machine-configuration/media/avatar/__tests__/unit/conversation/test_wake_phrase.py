import pathlib

from hypothesis import given
from hypothesis import strategies as st

from wake_phrase import (
    LiveSession,
    addressed_session,
    sessions_heard_anywhere,
    vocative_session,
)

IBARAKI = LiveSession("Ibaraki-dōji", "wW:pPY")
VOYAGER = LiveSession("Voyager", "wW:pPZ")
EDMOND = LiveSession("Edmond Dantès", "wW:pMX")
LIVE = [IBARAKI, VOYAGER, EDMOND]
ORDINARY_WORDS_FILE = pathlib.Path(__file__).parents[1] / "wake/ordinary-words.txt"
MESSAGE_WORDS = ["check", "the", "build", "roda", "os", "testes", "agora"]

message_words = st.lists(
    st.sampled_from(MESSAGE_WORDS),
    min_size=1,
    max_size=8,
).map(" ".join)


def first_name(session):
    return session.servant.replace("-", " ").split()[0]


@given(
    greeting=st.sampled_from(["hey", "Hey", "ei", "Oi", "ok", "E o"]),
    session=st.sampled_from(LIVE),
    message=message_words,
)
def test_a_greeting_and_a_live_name_carry_the_rest_of_the_breath(
    greeting, session, message
):
    match = addressed_session(f"{greeting} {first_name(session)}, {message}.", LIVE)
    assert match.session == session, "the spoken first name picks that session"
    assert match.message == message, "the words after the name are the message"


@given(session=st.sampled_from(LIVE), message=message_words)
def test_a_name_without_a_leading_greeting_wakes_nobody(session, message):
    name = first_name(session)
    assert addressed_session(f"{name} {message}", LIVE) is None, (
        "talking about an agent is not talking to it"
    )
    assert addressed_session(f"yesterday {name} said {message}", LIVE) is None


def test_a_misheard_name_still_reaches_its_session(monkeypatch):
    monkeypatch.setenv("AVATAR_ORDINARY_WORDS", str(ORDINARY_WORDS_FILE))
    match = addressed_session("Hey Iberaki, check the build.", LIVE)
    assert match.session == IBARAKI, (
        "transcription drift within the threshold is tolerated"
    )


def test_accents_and_case_do_not_matter():
    assert addressed_session("OI EDMOND, roda os testes", LIVE).session == EDMOND


def test_two_sessions_sharing_a_spoken_name_wake_neither():
    twins = [LiveSession("Orion", "wW:p1"), LiveSession("Orion Prime", "wW:p2")]
    assert addressed_session("hey Orion, status", twins) is None, (
        "an ambiguous name must not guess between sessions"
    )


def test_an_unknown_name_or_a_bare_greeting_wakes_nobody():
    assert addressed_session("hey Kevin, status", LIVE) is None
    assert addressed_session("hey", LIVE) is None
    assert addressed_session("", LIVE) is None


@given(session=st.sampled_from(LIVE), message=message_words)
def test_a_name_opening_or_closing_a_line_addresses_its_session(session, message):
    name = first_name(session)
    assert vocative_session(f"{name}, {message}", LIVE) == session
    assert vocative_session(f"oi {name} {message}", LIVE) == session
    assert vocative_session(f"{message}, {name}?", LIVE) == session


@given(session=st.sampled_from(LIVE), message=message_words)
def test_a_name_inside_a_line_addresses_nobody(session, message):
    line = f"yesterday {first_name(session)} said {message} again"
    assert vocative_session(line, LIVE) is None


def test_a_bare_greeting_addresses_nobody():
    assert vocative_session("hey", LIVE) is None
    assert vocative_session("", LIVE) is None


@given(
    session=st.sampled_from(LIVE),
    before=st.lists(st.sampled_from(MESSAGE_WORDS), max_size=6),
    after=st.lists(st.sampled_from(MESSAGE_WORDS), max_size=6),
)
def test_a_live_name_is_heard_at_any_position_of_a_line(session, before, after):
    line = " ".join([*before, first_name(session), *after])
    assert sessions_heard_anywhere(line, LIVE) == [session]


@given(pair=st.permutations(LIVE).map(lambda sessions: sessions[:2]))
def test_every_live_name_in_a_line_is_heard_once_in_spoken_order(pair):
    first, second = (first_name(session) for session in pair)
    line = f"ask {first} to tell {second} the build broke, {first}"
    assert sessions_heard_anywhere(line, LIVE) == pair


def test_a_line_without_a_unique_live_name_hears_nobody():
    twins = [LiveSession("Orion", "wW:p1"), LiveSession("Orion Prime", "wW:p2")]
    assert sessions_heard_anywhere("tell Orion to check the build", twins) == []
    assert sessions_heard_anywhere("roda os testes agora", LIVE) == []
    assert sessions_heard_anywhere("", LIVE) == []
