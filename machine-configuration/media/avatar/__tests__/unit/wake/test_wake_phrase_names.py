import pathlib

import pytest
from hypothesis import given
from hypothesis import strategies as st

from name_hearing import sound_key
from transcription.spoken_names import NICKNAMES, called_name
from wake_phrase import (
    GREETINGS,
    LiveSession,
    addressed_session,
    named_in_turn,
    spoken_name,
    vocative_session,
)

ROSTER = pathlib.Path(__file__).parents[6] / "agent-harness/servants/roster.txt"
SERVANTS = [line.split(" | ")[0] for line in ROSTER.read_text().splitlines() if line]
ORDINARY_WORDS_FILE = pathlib.Path(__file__).with_name("ordinary-words.txt")
SPOKEN_NAMES = {spoken_name(servant) for servant in SERVANTS}
ORDINARY_WORDS = [
    word for word in ORDINARY_WORDS_FILE.read_text().split() if word not in SPOKEN_NAMES
]
WHOLE_ROSTER = [
    LiveSession(servant, f"pane-{index}") for index, servant in enumerate(SERVANTS)
]
FEW_LIVE = [
    LiveSession(servant, f"pane-{index}")
    for index, servant in enumerate(
        [
            "Scheherazade",
            "Medea",
            "Circe",
            "Robin Hood",
            "Nikola Tesla",
            "Artoria Pendragon (Lancer)",
            "Sasaki Kojirou",
            "Passionlip",
        ]
    )
]


@pytest.fixture(autouse=True)
def ordinary_vocabulary(monkeypatch):
    monkeypatch.setenv("AVATAR_ORDINARY_WORDS", str(ORDINARY_WORDS_FILE))


def servant_matched_by(text, sessions):
    match = named_in_turn(text, sessions)
    return match.session.servant if match else None


def test_the_misheard_greeting_reaches_scheherazade_with_its_message():
    match = addressed_session("Hey, chise hresnade. How are you doing?", WHOLE_ROSTER)
    assert match.session.servant == "Scheherazade"
    assert match.message == "How are you doing"


def test_a_garbled_name_closing_a_line_addresses_its_servant():
    session = vocative_session("how are you doing chise hresnade", WHOLE_ROSTER)
    assert session.servant == "Scheherazade"


@pytest.mark.parametrize(
    ("heard", "servant"),
    [
        ("hey sherazade", "Scheherazade"),
        ("oi xerazade tudo bem", "Scheherazade"),
        ("hey shehrazad", "Scheherazade"),
        ("hey sirse", "Circe"),
        ("hey nicola", "Nikola Tesla"),
        ("hey artorya", "Artoria Pendragon (Lancer)"),
        ("hey passion lip", "Passionlip"),
    ],
)
def test_a_name_heard_wrong_still_reaches_its_servant(heard, servant):
    assert servant_matched_by(heard, FEW_LIVE) == servant


def test_every_nickname_belongs_to_a_roster_servant():
    assert set(NICKNAMES) <= {called_name(servant) for servant in SERVANTS}


@given(
    nicknamed=st.sampled_from(
        [
            (called, nickname)
            for called, names in NICKNAMES.items()
            for nickname in names
        ]
    )
)
def test_a_servant_answers_to_each_of_its_nicknames(nicknamed):
    called, nickname = nicknamed
    match = addressed_session(f"hey {nickname} status", WHOLE_ROSTER)
    assert called_name(match.session.servant) == called
    assert match.message == "status"


@pytest.mark.parametrize(
    ("heard", "servant"),
    [
        ("Hey Shera, how are you doing?", "Scheherazade"),
        ("Hey Shira, how are you doing?", "Scheherazade"),
        ("Hey Ozzie, how are you doing?", "Ozymandias"),
        ("Hey Ashiwaka, how are you doing?", "Ushiwakamaru"),
        ("Hey Katzall, how are you doing?", "Quetzalcoatl"),
        ("Hey Hokasai, how are you doing?", "Katsushika Hokusai"),
    ],
)
def test_a_nickname_as_hex_heard_it_reaches_its_servant(heard, servant):
    assert servant_matched_by(heard, WHOLE_ROSTER) == servant


@pytest.mark.parametrize(
    "heard",
    [
        "hey media player",
        "e agora",
        "oi cara",
        "hey girls",
        "hey so here is the thing",
        "oi tudo bem",
        "hi robot",
        "hey me",
    ],
)
def test_ordinary_speech_wakes_nobody(heard):
    assert named_in_turn(heard, WHOLE_ROSTER) is None


@given(
    greeting=st.sampled_from(sorted(GREETINGS) + [""]),
    words=st.lists(st.sampled_from(ORDINARY_WORDS), min_size=1, max_size=8),
)
def test_a_sentence_of_ordinary_words_wakes_nobody(greeting, words):
    sentence = " ".join([greeting, *words]).strip()
    assert named_in_turn(sentence, WHOLE_ROSTER) is None


def test_without_a_vocabulary_only_same_sounding_names_wake(monkeypatch):
    monkeypatch.setenv("AVATAR_ORDINARY_WORDS", "")
    assert servant_matched_by("hey sherazade", FEW_LIVE) == "Scheherazade"
    assert servant_matched_by("hey chise hresnade", FEW_LIVE) is None
    assert servant_matched_by("hey shehrazad", FEW_LIVE) is None


def test_a_tie_between_two_different_sessions_matches_nobody():
    twins = [LiveSession("Sasaki", "pane-1"), LiveSession("Sasuki", "pane-2")]
    assert addressed_session("hey sasaki", twins).session.servant == "Sasaki"
    assert addressed_session("hey sasoki", twins) is None


def test_spelling_variants_of_one_sound_share_a_key():
    assert sound_key("sherazade") == sound_key("xerazade") == sound_key("scherazade")
    assert sound_key("phil") == sound_key("fil")
    assert sound_key("kirke") == sound_key("qirke")


@given(servant=st.sampled_from(SERVANTS))
def test_every_roster_servant_alone_is_matched_by_its_first_name(servant):
    session = LiveSession(servant, "pane-0")
    match = addressed_session(f"hey {spoken_name(servant)} status", [session])
    assert match.session == session
    assert match.message == "status"


@given(first=st.sampled_from(SERVANTS), second=st.sampled_from(SERVANTS))
def test_two_sessions_with_different_spoken_names_never_both_match_one_exact_name(
    first, second
):
    sessions = [LiveSession(first, "pane-0"), LiveSession(second, "pane-1")]
    match = addressed_session(f"hey {spoken_name(first)} status", sessions)
    if spoken_name(first) == spoken_name(second):
        assert match is None
        return
    assert match is None or match.session == sessions[0]
