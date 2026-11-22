import io
import json
import threading
import urllib.error

import decisions_api
import pytest
from addressing_decision import (
    CONFIDENCE_FLOOR,
    HOLDER,
    NOBODY,
    QUESTION,
    Route,
    Turn,
    request,
    verdict,
)
from hypothesis import given
from hypothesis import strategies as st

SERVANTS = ["Ibaraki", "Medea", "Voyager", "Astolfo"]
CHOSEN = st.sampled_from([*SERVANTS, HOLDER, NOBODY, ""]) | st.none() | st.integers()
CONFIDENCES = st.floats() | st.integers() | st.booleans() | st.none() | st.text()
ANSWER = st.fixed_dictionaries(
    {},
    optional={
        "type": st.sampled_from(["choice", "refusal"]) | st.text(),
        "name": st.sampled_from([QUESTION, "other"]),
        "choice": CHOSEN,
        "confidence": CONFIDENCES,
    },
)
ANSWERS = st.lists(ANSWER | st.none() | st.text() | st.integers(), max_size=4)
CANDIDATES = st.lists(st.sampled_from(SERVANTS), min_size=1, unique=True)


def confident_choice_of(answer, value):
    confidence = answer.get("confidence")
    return (
        answer.get("type") == "choice"
        and answer.get("name") == QUESTION
        and answer.get("choice") == value
        and isinstance(confidence, int | float)
        and not isinstance(confidence, bool)
        and CONFIDENCE_FLOOR <= confidence <= 1
    )


@given(answers=ANSWERS, candidates=CANDIDATES)
def test_a_verdict_names_a_candidate_only_for_a_confident_choice_of_it(
    answers, candidates
):
    decided = verdict(answers, candidates)
    if decided.route is not Route.CANDIDATE:
        return
    assert decided.choice in candidates
    assert any(
        isinstance(answer, dict) and confident_choice_of(answer, decided.choice)
        for answer in answers
    )


@given(
    candidates=CANDIDATES,
    confidence=st.floats(min_value=CONFIDENCE_FLOOR, max_value=1),
    data=st.data(),
)
def test_a_confident_choice_of_a_candidate_names_it(candidates, confidence, data):
    chosen = data.draw(st.sampled_from(candidates))
    answer = {"type": "choice", "name": QUESTION, "choice": chosen}
    decided = verdict([answer | {"confidence": confidence}], candidates)
    assert (decided.route, decided.choice) == (Route.CANDIDATE, chosen)


@pytest.mark.parametrize(
    ("answers", "route"),
    [
        ([{"type": "refusal", "name": QUESTION}], Route.KEEP),
        ([{"type": "choice", "name": QUESTION, "choice": HOLDER}], Route.KEEP),
        ([{"type": "choice", "name": QUESTION, "choice": NOBODY}], Route.NOBODY),
        ([], Route.KEEP),
    ],
)
def test_every_answer_but_a_confident_candidate_moves_nobody(answers, route):
    assert verdict(answers, SERVANTS).route is route


@given(holder=st.sampled_from([None, "Ishtar"]), candidates=CANDIDATES)
def test_the_question_offers_the_holder_each_candidate_and_nobody_once(
    holder, candidates
):
    input_messages, questions = request("Medea, status", (), holder, candidates)
    values = [choice["value"] for choice in questions[0]["choices"]]
    assert values == [*([HOLDER] if holder else []), *candidates, NOBODY]
    assert questions[0]["name"] == QUESTION and questions[0]["type"] == "choice"
    assert input_messages[0]["role"] == "developer"
    assert input_messages[-1] == {"role": "user", "content": "Medea, status"}


def test_earlier_turns_precede_the_utterance_with_who_spoke():
    turns = (Turn("Lucas", "first words"), Turn(None, "second words"))
    input_messages, _ = request("Medea?", turns, "Ishtar", ["Medea"])
    earlier = [message["content"] for message in input_messages[1:-1]]
    assert "Lucas" in earlier[0] and "first words" in earlier[0]
    assert "second words" in earlier[1]


@pytest.fixture
def keyed(monkeypatch, tmp_path):
    key = tmp_path / "openai-api-key"
    key.write_text("the-key\n")
    monkeypatch.setattr(decisions_api, "KEY_FILE", key)


def replying(monkeypatch, reply):
    sent = []

    def urlopen(request, timeout):
        sent.append((request, timeout))
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(reply)

    monkeypatch.setattr(decisions_api.urllib.request, "urlopen", urlopen)
    return sent


def test_the_decisions_api_is_asked_with_the_key_and_its_answers_returned(
    monkeypatch, keyed
):
    answers = [{"type": "choice", "name": QUESTION, "choice": "Medea"}]
    sent = replying(monkeypatch, json.dumps({"answers": answers}).encode())
    assert decisions_api.answers(["input"], ["questions"]) == answers
    ((posted, timeout),) = sent
    assert posted.full_url == "https://api.openai.com/v1/decisions"
    assert posted.method == "POST"
    assert posted.get_header("Authorization") == "Bearer the-key"
    assert json.loads(posted.data) == {
        "model": decisions_api.MODEL,
        "input": ["input"],
        "questions": ["questions"],
    }
    assert timeout == decisions_api.TIMEOUT_SECONDS


@pytest.mark.parametrize(
    "reply",
    [
        urllib.error.HTTPError("https://api.openai.com", 500, "down", {}, None),
        urllib.error.URLError("unreachable"),
        b"not json",
        b'{"answers": "none"}',
        b"[]",
    ],
)
def test_a_failed_reply_raises_what_the_wake_falls_back_on(monkeypatch, keyed, reply):
    replying(monkeypatch, reply)
    with pytest.raises((OSError, ValueError)):
        decisions_api.answers([], [])


def test_a_missing_key_raises_before_anything_is_sent(monkeypatch):
    sent = replying(monkeypatch, b"{}")
    with pytest.raises(OSError):
        decisions_api.answers([], [])
    assert sent == []


def test_a_slow_reply_times_out(monkeypatch, keyed):
    released = threading.Event()
    monkeypatch.setattr(decisions_api, "TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(
        decisions_api.urllib.request, "urlopen", lambda *_, **__: released.wait(1)
    )
    with pytest.raises(TimeoutError):
        decisions_api.answers([], [])
    released.set()
