import itertools
import json
from unittest.mock import Mock

import pytest
import wake_listener
from addressing_decision import CONFIDENCE_FLOOR, QUESTION
from conversation_addressee import Addressee
from conversation_seat import Seat
from wake_fakes import IBARAKI, UNREACHABLE, VOYAGER, answered, boundaries, deciding

HELD_BY_VOYAGER = Addressee(VOYAGER.pane, VOYAGER.servant, 0)


def conversation(decided, **changes):
    fakes = boundaries(
        sessions=(VOYAGER, IBARAKI),
        addressee=Mock(return_value=HELD_BY_VOYAGER),
        conversation_listening=Mock(return_value=True),
        decide=deciding(decided),
        **changes,
    )
    listener = wake_listener.WakeListener(fakes, dry_run=False)
    listener.start_reading_conversation()
    return fakes, listener


def say(fakes, listener, *turns):
    fakes.transcript_entries.return_value = [
        {"sequence": sequence, "text": text, "source": source}
        for sequence, (text, source) in enumerate(turns, start=1)
    ]
    listener.read_conversation()


def heard_in_conversation(text, decided, source="human", **changes):
    fakes, listener = conversation(decided, **changes)
    say(fakes, listener, (text, source))
    return fakes


def decisions(fakes):
    lines = [call.args[0] for call in fakes.report.call_args_list]
    records = [json.loads(line) for line in lines if line.startswith("{")]
    return [record for record in records if record.get("decision") == "addressing"]


def test_mentioning_another_servant_keeps_the_floor():
    fakes = heard_in_conversation("I told Ibaraki the build broke", answered("holder"))
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()
    (decision,) = decisions(fakes)
    assert (decision["verdict"], decision["choice"]) == ("keep", "holder")


def test_turning_to_another_servant_without_a_greeting_hands_over_the_floor():
    fakes = heard_in_conversation("Ibaraki, can you check it?", answered("Ibaraki"))
    assert fakes.hand_to.call_args.args[0] == Addressee(
        IBARAKI.pane, IBARAKI.servant, 1
    )
    pane, text, _ = fakes.prompt_now.call_args.args
    assert pane == IBARAKI.pane and "Ibaraki, can you check it " in text


@pytest.mark.parametrize(
    "decided",
    [
        answered("Ibaraki", CONFIDENCE_FLOOR - 0.01),
        [{"type": "refusal", "name": QUESTION}],
        answered("Medea"),
    ],
    ids=["below the floor", "refusal", "unknown servant"],
)
def test_an_unsure_refused_or_unknown_answer_keeps_the_floor(decided):
    fakes = heard_in_conversation("Ibaraki, status", decided)
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()
    assert decisions(fakes)[0]["verdict"] == "keep"


def test_a_chosen_servant_that_left_while_deciding_keeps_the_floor():
    fakes, listener = conversation(answered("Ibaraki"))

    def leaving(*_):
        fakes.sessions.return_value = [VOYAGER]
        return answered("Ibaraki")

    fakes.decide.side_effect = leaving
    say(fakes, listener, ("Ibaraki, status", "human"))
    fakes.hand_to.assert_not_called()
    assert "Ibaraki-dōji left" in fakes.report.call_args.args[0]


@pytest.mark.parametrize(
    ("text", "handed"), [("hey Ibaraki, status", True), ("Ibaraki, status", False)]
)
def test_without_the_decisions_api_the_greeting_rule_moves_the_floor(text, handed):
    fakes = heard_in_conversation(text, UNREACHABLE)
    assert fakes.hand_to.called is handed
    (decision,) = decisions(fakes)
    assert decision["fallback"] == str(UNREACHABLE)


def test_a_silent_timeout_is_logged_by_its_kind():
    fakes = heard_in_conversation("hey Ibaraki, status", TimeoutError())
    assert decisions(fakes)[0]["fallback"] == "TimeoutError"


@pytest.mark.parametrize(
    ("source", "seat"),
    [("meeting", Seat.ROOM), (None, Seat.ROOM), ("human", Seat.DISCORD)],
)
def test_speech_not_from_the_room_microphone_never_reaches_the_api(source, seat):
    fakes = heard_in_conversation(
        "hey Ibaraki, status",
        answered("Ibaraki"),
        source=source,
        open_seat=Mock(return_value=seat),
    )
    fakes.decide.assert_not_called()
    assert fakes.hand_to.call_args.args[0].pane == IBARAKI.pane


@pytest.mark.parametrize(
    "text", ["roda os testes e manda o resultado", "Voyager, keep going"]
)
def test_speech_naming_no_other_live_servant_never_reaches_the_api(text):
    fakes = heard_in_conversation(text, answered("Ibaraki"))
    fakes.decide.assert_not_called()
    fakes.hand_to.assert_not_called()


def test_the_decision_is_logged_before_the_floor_moves():
    order = Mock()
    fakes = heard_in_conversation(
        "Ibaraki, status",
        answered("Ibaraki"),
        report=order.report,
        hand_to=order.hand_to,
        now=Mock(side_effect=itertools.count(0.0, 0.25)),
    )
    (decision,) = decisions(fakes)
    steps = [name for name, *_ in order.mock_calls]
    reported = [call.args[0] for call in order.mock_calls]
    logged = reported.index(json.dumps(decision, ensure_ascii=False))
    assert logged < steps.index("hand_to")
    assert decision["phase"] == "conversation" and decision["sequence"] == 1
    assert decision["candidates"] == ["Ibaraki"]
    assert (decision["verdict"], decision["confidence"]) == ("candidate", 0.97)
    assert decision["latency_ms"] == 250


def test_the_decision_hears_the_last_six_microphone_turns_and_no_meeting_voice():
    fakes, listener = conversation(answered("holder"))
    earlier = [(f"turn {number}", "human") for number in range(8)]
    say(fakes, listener, *earlier, ("secret plans", "meeting"), ("Ibaraki?", "human"))
    contents = [message["content"] for message in fakes.decide.call_args.args[0]]
    assert [n for n in range(8) if any(f"turn {n}" in c for c in contents)] == list(
        range(2, 8)
    )
    assert not any("secret" in content for content in contents)
    assert contents[-1] == "Ibaraki?"
