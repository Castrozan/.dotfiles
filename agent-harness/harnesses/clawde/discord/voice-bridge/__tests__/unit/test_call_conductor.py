import asyncio
import json

import pytest

from voice_bridge.call_conductor import (
    FAILED_TURN_APOLOGY,
    HermesTurnError,
    STAY_SILENT_REPLY,
    answer_spoken_lines,
    final_reply_from_turn_events,
    reply_worth_speaking,
    spoken_turn_prompt,
)


def conversation_outcome(queued_lines, reply_to):
    async def scenario():
        pending_lines = asyncio.Queue()
        for line in queued_lines:
            pending_lines.put_nowait(line)
        spoken = []

        async def speak(text):
            spoken.append(text)

        answering = asyncio.create_task(
            answer_spoken_lines(pending_lines, reply_to, speak)
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        answering.cancel()
        return spoken

    return asyncio.run(scenario())


def test_lines_spoken_while_silver_was_busy_form_one_turn():
    prompts = []

    async def reply_to(prompt):
        prompts.append(prompt)
        return "Oi."

    spoken = conversation_outcome(["tudo", "bem?"], reply_to)

    assert len(prompts) == 1
    assert prompts[0].endswith("Lucas: tudo bem?")
    assert spoken == ["Oi."]


def test_silver_stays_quiet_when_it_judges_the_line_noise():
    async def reply_to(_prompt):
        return f"{STAY_SILENT_REPLY}."

    assert conversation_outcome(["ruído"], reply_to) == []


def test_a_failed_turn_is_said_out_loud_instead_of_going_silent():
    async def reply_to(_prompt):
        raise HermesTurnError("turn_timed_out")

    assert conversation_outcome(["oi"], reply_to) == [FAILED_TURN_APOLOGY]


def test_the_final_reply_comes_from_the_result_event_past_the_trailer():
    turn_output = "\n".join(
        [
            json.dumps({"type": "text", "text": "partial"}),
            json.dumps({"type": "result", "text": "Sim."}),
            "",
            "session_id: local-1",
        ]
    )

    assert final_reply_from_turn_events(turn_output) == "Sim."


def test_a_turn_without_a_result_event_is_an_error():
    with pytest.raises(HermesTurnError):
        final_reply_from_turn_events("session_id: local-1")


def test_an_empty_reply_is_not_spoken():
    assert not reply_worth_speaking("")
    assert reply_worth_speaking("Oi.")


def test_the_prompt_tells_silver_how_to_stay_silent():
    assert STAY_SILENT_REPLY in spoken_turn_prompt(["oi"])
