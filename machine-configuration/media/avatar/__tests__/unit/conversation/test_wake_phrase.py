from hypothesis import given
from hypothesis import strategies as st

from wake_phrase import LiveSession, addressed_session, vocative_session

IBARAKI = LiveSession("Ibaraki-dōji", "wW:pPY")
VOYAGER = LiveSession("Voyager", "wW:pPZ")
EDMOND = LiveSession("Edmond Dantès", "wW:pMX")
LIVE = [IBARAKI, VOYAGER, EDMOND]

message_words = st.lists(
    st.sampled_from(["check", "the", "build", "roda", "os", "testes", "agora"]),
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


def test_a_misheard_name_still_reaches_its_session():
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
