import json
import math
import re
import time

import pytest
from hypothesis import given
from hypothesis import strategies as st

import openai_decisions_api
import workflow_decision
from decision_choice import DecisionRequest, Option, decide

LEGAL = ("retry", "retry-deeper", "escalate")
FLOOR = 0.6
METRIC_NAME = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)*$")

json_values = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=True, allow_infinity=True)
    | st.text(max_size=8),
    lambda children: (
        st.lists(children, max_size=4)
        | st.dictionaries(st.text(max_size=8), children, max_size=4)
    ),
    max_leaves=12,
)
near_answers = st.fixed_dictionaries(
    {
        "name": st.sampled_from(["next", "merge"]) | json_values,
        "type": st.sampled_from(["choice", "score"]) | json_values,
        "choice": st.sampled_from([*LEGAL, "done", "merge"]) | json_values,
        "confidence": st.floats(-1, 2)
        | st.just(math.nan)
        | st.booleans()
        | json_values,
    }
)
well_formed_answers = st.fixed_dictionaries(
    {
        "name": st.just("next"),
        "type": st.sampled_from(["choice", "score"]),
        "choice": st.sampled_from([*LEGAL, "done", "merge", ""]),
        "confidence": st.floats(0, 1),
    }
)
replies = (
    json_values
    | st.fixed_dictionaries(
        {"answers": st.lists(near_answers, max_size=3) | json_values}
    )
    | st.fixed_dictionaries(
        {"answers": st.lists(well_formed_answers, min_size=1, max_size=2)}
    )
)


def request_with(options: tuple[str, ...], guarded: bool = False) -> DecisionRequest:
    return DecisionRequest(
        decision="next",
        instructions="Which next step?",
        context="A fix loop.",
        evidence="The test fails.",
        options=tuple(Option(option, f"{option} it") for option in options),
        safest="escalate",
        floor=FLOOR,
        reason="the test still fails",
        guarded=guarded,
        summary="Iteration 1.",
    )


def confident_legal_answer(replied: object) -> dict | None:
    answers = replied.get("answers") if isinstance(replied, dict) else None
    named = [
        answer
        for answer in (answers if isinstance(answers, list) else [])
        if isinstance(answer, dict) and answer.get("name") == "next"
    ]
    if not named or named[0].get("type") != "choice":
        return None
    answer = named[0]
    confidence = answer.get("confidence")
    legal_choice = isinstance(answer.get("choice"), str) and answer["choice"] in LEGAL
    numeric = isinstance(confidence, int | float) and not isinstance(confidence, bool)
    confident = numeric and math.isfinite(confidence) and FLOOR <= confidence <= 1
    return answer if legal_choice and confident else None


@given(replied=replies)
def test_any_reply_yields_a_legal_option_and_misses_yield_escalate(replied):
    decision = decide(request_with(LEGAL), lambda *_: replied).decision
    expected = confident_legal_answer(replied)
    assert decision.choice in LEGAL
    if expected is None:
        assert (decision.choice, decision.source) == ("escalate", "fallback")
    else:
        assert (decision.choice, decision.source) == (expected["choice"], "model")


@given(error=st.sampled_from([OSError, ValueError, TimeoutError, ConnectionError]))
def test_a_failed_or_slow_call_yields_escalate(error):
    def failing(*_):
        raise error("no answer")

    consultation = decide(request_with(LEGAL), failing)
    assert consultation.decision.choice == "escalate"
    assert consultation.decision.source == "fallback"
    assert consultation.model_calls == 1


@given(option=st.sampled_from(["done", "escalate", "merge"]), guarded=st.booleans())
def test_a_single_legal_option_is_chosen_without_a_call(option, guarded):
    def never(*_):
        raise AssertionError("asked the Decisions API for a settled decision")

    consultation = decide(request_with((option,), guarded), never)
    assert consultation.decision.choice == option
    assert consultation.decision.source == ("guard" if guarded else "only-option")
    assert consultation.model_calls == 0


def test_the_port_bounds_a_slow_reply(monkeypatch, tmp_path):
    key_file = tmp_path / "openai-api-key"
    key_file.write_text("test-key\n")
    monkeypatch.setattr(openai_decisions_api, "KEY_FILE", key_file)
    monkeypatch.setattr(openai_decisions_api, "posted", lambda *_: time.sleep(1))
    with pytest.raises(TimeoutError):
        openai_decisions_api.reply([], [], timeout_seconds=0.05)


def test_a_missing_key_file_falls_back(monkeypatch, tmp_path):
    monkeypatch.setattr(openai_decisions_api, "KEY_FILE", tmp_path / "absent")
    consultation = decide(request_with(LEGAL), openai_decisions_api.reply)
    assert consultation.decision.source == "fallback"


def request_document(options: list[str], safest: str) -> dict:
    return {
        "decision": "merge",
        "instructions": "Merge?",
        "context": "A fix loop.",
        "evidence": "Green.",
        "options": [{"id": option, "description": option} for option in options],
        "safest": safest,
        "floor": FLOOR,
        "reason": "green",
        "guarded": False,
        "summary": "Push?",
    }


def test_a_request_must_keep_the_safest_option_legal_when_the_model_chooses():
    with pytest.raises(SystemExit):
        workflow_decision.parsed_request(
            request_document(["merge", "hold"], "escalate")
        )
    with pytest.raises(SystemExit):
        workflow_decision.parsed_request(request_document([], "escalate"))


@given(replied=replies)
def test_the_rendered_decision_feeds_the_wait_and_archon_metrics(replied):
    request = workflow_decision.parsed_request(
        request_document(["merge", "escalate"], "escalate")
    )
    rendered = workflow_decision.rendered(request, decide(request, lambda *_: replied))
    assert rendered["recommendation"]["option"] in rendered["options"]
    assert rendered["needs_human"] == (rendered["choice"] == "escalate")
    assert all(METRIC_NAME.match(record["name"]) for record in rendered["metrics"])
    assert all(record["value"] >= 0 for record in rendered["metrics"])
    json.dumps(rendered, allow_nan=False)
