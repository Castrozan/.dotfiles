from hypothesis import given
from hypothesis import strategies as st

from spoken_turns import Party, SpokenTurn, TurnAssembler

SETTLE_SECONDS = 1.0
pieces = st.lists(
    st.tuples(st.sampled_from(list(Party)), st.text(min_size=1, max_size=8)),
    max_size=20,
)


def runs_of(additions):
    runs = []
    for party, text in additions:
        if runs and runs[-1][0] == party:
            runs[-1] = (party, runs[-1][1] + text)
        else:
            runs.append((party, text))
    return [SpokenTurn(party, text.strip()) for party, text in runs if text.strip()]


@given(pieces)
def test_every_change_of_speaker_finishes_the_previous_turn_whole(additions):
    assembler = TurnAssembler(SETTLE_SECONDS)
    finished = []
    for moment, (party, text) in enumerate(additions):
        finished += assembler.add(party, text, moment * 0.1)
    finished += assembler.finish()
    assert finished == runs_of(additions)


def test_a_turn_finishes_only_after_the_speaker_pauses_long_enough():
    assembler = TurnAssembler(SETTLE_SECONDS)
    assembler.add(Party.HUMAN, "Hey Voyager, ", 0.0)
    assembler.add(Party.HUMAN, "check the build", 0.5)
    assert assembler.settled(1.4) == []
    assert assembler.settled(1.5) == [
        SpokenTurn(Party.HUMAN, "Hey Voyager, check the build")
    ]
    assert assembler.settled(9.0) == []
