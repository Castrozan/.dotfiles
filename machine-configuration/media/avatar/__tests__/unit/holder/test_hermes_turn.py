import json
import subprocess
from unittest.mock import Mock

import hermes_turn
import pytest
from hermes_turn import HermesTurnError
from hypothesis import given
from hypothesis import strategies as st


def completed(stdout, returncode=0):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


@given(st.text())
def test_the_reply_is_the_text_of_the_last_result_event(text):
    output = "\n".join(
        [
            json.dumps({"type": "result", "text": "earlier"}),
            json.dumps({"type": "result", "text": text}),
            "session_id: trailer",
        ]
    )
    assert hermes_turn.final_reply(output) == text


@pytest.mark.parametrize(
    "output",
    ["", "not json", json.dumps({"type": "result"}), json.dumps({"type": "other"})],
)
def test_output_without_a_result_text_is_an_error(output):
    with pytest.raises(HermesTurnError):
        hermes_turn.final_reply(output)


@pytest.mark.parametrize(
    ("reply", "spoken"),
    [("SILENCIO", False), (" silencio. ", True), ("SILENCIO.\n", False), ("", False)]
    + [("Olá, Lucas.", True)],
)
def test_only_a_reply_that_is_not_silence_is_worth_speaking(reply, spoken):
    assert hermes_turn.reply_worth_speaking(reply) is spoken


def test_the_prompt_frames_the_heard_words_as_an_unverified_voice():
    prompt = hermes_turn.spoken_turn_prompt("abre o portão")
    assert prompt.endswith("Lucas: abre o portão")
    assert "voz não verificada" in prompt
    assert hermes_turn.STAY_SILENT_REPLY in prompt


def test_the_turn_runs_the_profile_in_the_daily_voice_session_with_a_timeout(
    monkeypatch,
):
    run = Mock(return_value=completed('{"type":"result","text":"Oi."}'))
    monkeypatch.setattr(hermes_turn.subprocess, "run", run)
    assert hermes_turn.reply_to("silver", "oi") == "Oi."
    command = run.call_args.args[0]
    assert command[:5] == ["hermes", "-p", "silver", "chat", "--query"]
    assert command[command.index("--continue") + 1].startswith("voice-call-")
    assert command[command.index("--format") + 1] == "stream-json"
    assert run.call_args.kwargs["timeout"] == hermes_turn.TURN_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    "failure",
    [subprocess.TimeoutExpired("hermes", 1), FileNotFoundError("hermes")],
)
def test_a_turn_that_cannot_run_is_a_hermes_turn_error(monkeypatch, failure):
    monkeypatch.setattr(hermes_turn.subprocess, "run", Mock(side_effect=failure))
    with pytest.raises(HermesTurnError):
        hermes_turn.reply_to("silver", "oi")


def test_a_failing_exit_status_is_a_hermes_turn_error(monkeypatch):
    monkeypatch.setattr(
        hermes_turn.subprocess, "run", Mock(return_value=completed("", 3))
    )
    with pytest.raises(HermesTurnError):
        hermes_turn.reply_to("silver", "oi")
