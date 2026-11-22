from unittest.mock import Mock

import addressing_decision
import listener
import listener_runtime
import quiet_conversation
import utterances
import wake_boundaries
import wake_listener
from conversation_addressee import Addressee
from hypothesis import given, strategies
from pending_speech import PendingSpeech
from wake_fakes import VOYAGER, answered, boundaries
from wake_phrase import LiveSession

QUIET = utterances.UNFINISHED_TURN_SETTLE_SECONDS
POLL = quiet_conversation.TRANSCRIPT_POLL_SECONDS
ANASTASIA = LiveSession("Anastasia", "wW:pSP")
TAMAMO = LiveSession("Tamamo Cat", "wW:pTC")
ASTOLFO = LiveSession("Astolfo", "wW:pAS")
HESITATION = {
    "sequence": 71,
    "time": 1795382239.642473,
    "source": "human",
    "text": "Hã, bom",
    "speaker": None,
    "turn_finished": False,
}
TURNING_TO_TAMAMO = {
    "sequence": 72,
    "time": 1795382253.6834095,
    "source": "human",
    "text": (
        "Okay. I-if now I speak with Tamamo Cat, uh, will she reply to me? "
        "Tamamo, how is the work going? I don't remember what were you doing"
    ),
    "speaker": None,
    "turn_finished": False,
}
MUSING = ["I haven't said hey or something yet. Uh, I think", "Astolfo, Astolfo"]


def held_by(holder, sessions, decided):
    fakes = boundaries(
        sessions=sessions,
        addressee=Mock(return_value=Addressee(holder.pane, holder.servant, 0)),
        conversation_listening=Mock(return_value=True),
        decide=Mock(return_value=decided),
    )
    listener = wake_listener.WakeListener(fakes, dry_run=False)
    listener.start_reading_conversation()
    return fakes, listener


def read_at(fakes, listener, moment, entries, speaking=False):
    fakes.now.return_value = moment
    fakes.transcript_entries.return_value = entries
    fakes.speech_in_progress.return_value = speaking
    listener.read_conversation()


def decided_text(fakes):
    return fakes.decide.call_args.args[0][-1]["content"]


def test_turning_to_tamamo_cat_and_falling_silent_hands_her_the_floor():
    fakes, listener = held_by(ANASTASIA, (ANASTASIA, TAMAMO), answered("Tamamo", 0.95))
    arrived = TURNING_TO_TAMAMO["time"] - HESITATION["time"]
    spoken = [HESITATION, TURNING_TO_TAMAMO]
    read_at(fakes, listener, 0.0, spoken[:1])
    read_at(fakes, listener, QUIET, spoken[:1])
    read_at(fakes, listener, arrived, spoken)
    read_at(fakes, listener, arrived + QUIET - POLL, spoken)
    fakes.hand_to.assert_not_called()
    read_at(fakes, listener, arrived + QUIET + POLL, spoken)
    fakes.hand_to.assert_called_once_with(
        Addressee(TAMAMO.pane, TAMAMO.servant, heard_through=72)
    )
    assert fakes.prompt_now.call_args.args[0] == TAMAMO.pane
    assert decided_text(fakes) == TURNING_TO_TAMAMO["text"]
    read_at(fakes, listener, arrived + 10 * QUIET, spoken)
    assert fakes.decide.call_count == 1
    assert fakes.hand_to.call_count == 1


def test_a_name_ending_a_sentence_still_being_spoken_is_judged_with_its_start():
    fakes, listener = held_by(
        VOYAGER, (VOYAGER, ASTOLFO), answered(addressing_decision.HOLDER, 0.9)
    )
    spoken = [
        {"sequence": 16, "source": "human", "text": MUSING[0], "turn_finished": False},
        {"sequence": 17, "source": "human", "text": MUSING[1], "turn_finished": True},
    ]
    read_at(fakes, listener, 0.0, spoken[:1])
    read_at(fakes, listener, 3 * QUIET, spoken[:1], speaking=True)
    fakes.decide.assert_not_called()
    read_at(fakes, listener, 3 * QUIET + POLL, spoken)
    read_at(fakes, listener, 9 * QUIET, spoken)
    assert fakes.decide.call_count == 1
    assert decided_text(fakes) == " ".join(MUSING)
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()


def test_a_finished_turn_is_judged_at_once_and_never_again_in_the_quiet():
    fakes, listener = held_by(VOYAGER, (VOYAGER, ASTOLFO), answered("Astolfo"))
    spoken = [{"sequence": 3, "source": "human", "text": "Astolfo, status"}]
    read_at(fakes, listener, 0.0, spoken)
    assert fakes.hand_to.call_args.args[0].pane == ASTOLFO.pane
    read_at(fakes, listener, 9 * QUIET, spoken)
    assert fakes.decide.call_count == 1
    assert fakes.hand_to.call_count == 1


def test_the_avatar_host_wake_sees_the_listener_speech_marker(monkeypatch, tmp_path):
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    speech = wake_boundaries.Boundaries().speech_in_progress
    pending = PendingSpeech(tmp_path / listener.SPEECH_IN_PROGRESS_MARKER)
    assert speech() is False
    pending.begin()
    assert speech() is True
    pending.finish()
    assert speech() is False


FRAGMENTS = strategies.lists(
    strategies.tuples(
        strategies.booleans(),
        strategies.floats(min_value=0, max_value=3 * QUIET),
        strategies.booleans(),
        strategies.booleans(),
    ),
    max_size=40,
)


@given(FRAGMENTS)
def test_every_fragment_lands_in_exactly_one_turn_in_order(fragments):
    transcript = quiet_conversation.ConversationTranscript()
    turns, spoken, now = [], [], 0.0
    for sequence, (finished, gap, by_the_avatar, speaking) in enumerate(fragments):
        now += gap
        turns.append(transcript.turn_ended_in_quiet(now, Mock(return_value=speaking)))
        entry = {
            "sequence": sequence,
            "source": "human",
            "speaker": "avatar" if by_the_avatar else None,
            "text": f"fragment{sequence}",
            "turn_finished": finished,
        }
        turns.append(transcript.completed_turn(entry, now))
        spoken += [] if by_the_avatar else [(entry["text"], finished)]
    turns.append(transcript.turn_ended_in_quiet(now + QUIET, Mock(return_value=False)))
    completed = [turn for turn in turns if turn is not None]
    words = [word for turn in completed for word in turn["text"].split()]
    assert words == [text for text, _ in spoken]
    endings = [turn["text"].split()[-1] for turn in completed]
    assert {text for text, finished in spoken if finished} <= set(endings)
    assert endings == [f"fragment{turn['sequence']}" for turn in completed]
