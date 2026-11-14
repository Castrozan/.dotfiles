import gpt_live
import transcript_log
import voice_session
from hypothesis import given
from hypothesis import strategies as st
from spoken_turns import Party, SpokenTurn

LUCAS_NAMES_SASAKI = SpokenTurn(Party.HUMAN, "Lucas: hey Sasaki")

ENTRIES = st.lists(
    st.fixed_dictionaries(
        {
            "source": st.sampled_from(["human", "avatar"]),
            "speaker": st.sampled_from([None, "Lucas"]),
            "text": st.text(min_size=1, max_size=900),
        }
    ),
    max_size=200,
)


@given(entries=ENTRIES)
def test_the_earlier_conversation_is_the_latest_turns_that_fit(entries):
    original = transcript_log.read_since
    transcript_log.read_since = lambda path, sequence: entries
    try:
        seeded = voice_session.earlier_conversation("transcript.jsonl")
    finally:
        transcript_log.read_since = original
    expected = [voice_session.spoken_turn(entry) for entry in entries]
    assert seeded == expected[len(expected) - len(seeded) :]
    assert len(seeded) <= voice_session.EARLIER_CONVERSATION_TURNS
    sizes = [len(turn.text) for turn in seeded]
    assert sum(sizes) <= voice_session.EARLIER_CONVERSATION_CHARACTERS
    dropped = expected[: len(expected) - len(seeded)]
    if dropped and len(seeded) < voice_session.EARLIER_CONVERSATION_TURNS:
        assert (
            sum(sizes) + len(dropped[-1].text)
            > voice_session.EARLIER_CONVERSATION_CHARACTERS
        )


def test_the_avatar_and_named_speakers_keep_their_parts():
    assert voice_session.spoken_turn(
        {"source": "avatar", "speaker": "avatar", "text": "Oi"}
    ) == SpokenTurn(Party.AVATAR, "Oi")
    assert voice_session.spoken_turn(
        {"source": "human", "speaker": "Lucas", "text": "hey"}
    ) == SpokenTurn(Party.HUMAN, "Lucas: hey")


def test_a_new_live_session_starts_from_the_conversation_so_far():
    fresh = gpt_live.GptLive("meridian")
    taking_over = gpt_live.GptLive(
        "meridian", [LUCAS_NAMES_SASAKI, SpokenTurn(Party.AVATAR, "Oi, Lucas")]
    )
    assert fresh.instructions == gpt_live.INSTRUCTIONS and fresh.history == []
    assert taking_over.instructions.startswith(gpt_live.INSTRUCTIONS)
    assert taking_over.instructions != gpt_live.INSTRUCTIONS
    assert taking_over.history == [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Lucas: hey Sasaki"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Oi, Lucas"}],
        },
    ]
