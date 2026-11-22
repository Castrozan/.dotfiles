import io
import json
import re
import urllib.error
from unittest.mock import MagicMock, Mock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from transcription import cloud_transcriber
from transcription import spoken_languages
from transcription import transcriber

SEGMENT = b"\x00\x00" * 1600
SPOKEN_CODES = ("pt", "por", "en", "eng", "ja", "jpn", "es", "spa")
DETECTED_CODES = st.one_of(st.none(), st.text(), st.sampled_from(SPOKEN_CODES))
NO_FIXTURE_CHECK = settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100
)
LANGUAGE_FIELD = re.compile(rb'name="language_code"\r\n\r\n(.*?)\r\n')


@pytest.fixture(autouse=True)
def fresh_recent_language(monkeypatch):
    monkeypatch.delenv("AVATAR_SERVANT_ROSTER", raising=False)
    monkeypatch.setattr(
        cloud_transcriber, "recent_language", spoken_languages.RecentLanguage()
    )


def scribe_response(payload):
    response = MagicMock()
    response.__enter__.return_value = io.BytesIO(json.dumps(payload).encode())
    return response


def stub_scribe_answers(monkeypatch, *answers):
    outcomes = [
        answer if isinstance(answer, Exception) else scribe_response(answer)
        for answer in answers
    ]
    urlopen = Mock(side_effect=outcomes)
    monkeypatch.setattr(cloud_transcriber.urllib.request, "urlopen", urlopen)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    return urlopen


def detected(text, language_code, language_probability=0.99):
    return {
        "text": text,
        "language_code": language_code,
        "language_probability": language_probability,
    }


def requested_languages(urlopen):
    fields = [
        LANGUAGE_FIELD.search(call.args[0].data) for call in urlopen.call_args_list
    ]
    return [field and field.group(1).decode() for field in fields]


@pytest.mark.parametrize("code", SPOKEN_CODES)
def test_a_spoken_language_is_accepted_after_one_request(monkeypatch, code):
    urlopen = stub_scribe_answers(monkeypatch, detected("bom dia", code))
    assert cloud_transcriber.transcribe(SEGMENT) == "bom dia"
    assert requested_languages(urlopen) == [None]


@pytest.mark.parametrize("code", ["fra", "rus"])
def test_an_unspoken_language_is_asked_again_pinned_to_portuguese(monkeypatch, code):
    urlopen = stub_scribe_answers(
        monkeypatch,
        detected("Pour le seul public", code, 0.61),
        detected("pode ser público", "por"),
    )
    assert cloud_transcriber.transcribe(SEGMENT) == "pode ser público"
    assert requested_languages(urlopen) == [None, "pt"]


@pytest.mark.parametrize(
    ("earlier", "code", "pinned"),
    [
        ("eng", "pt", "pt"),
        ("eng", "por", "pt"),
        ("jpn", "en", "en"),
        ("jpn", "eng", "en"),
        ("eng", "ja", "ja"),
        ("eng", "jpn", "ja"),
        ("eng", "es", "es"),
        ("eng", "spa", "es"),
    ],
)
def test_the_pinned_language_is_the_latest_spoken_one_in_either_code_form(
    monkeypatch, earlier, code, pinned
):
    urlopen = stub_scribe_answers(
        monkeypatch,
        detected("one", earlier),
        detected("two", code),
        detected("três", "fra"),
        detected("three", pinned),
    )
    texts = [cloud_transcriber.transcribe(SEGMENT) for _ in range(3)]
    assert texts == ["one", "two", "three"]
    assert requested_languages(urlopen) == [None, None, None, pinned]


def test_an_unspoken_detection_does_not_replace_the_pinned_language(monkeypatch):
    urlopen = stub_scribe_answers(
        monkeypatch,
        detected("hello", "eng"),
        detected("Bonjour", "fra"),
        detected("hello again", "eng"),
        detected("Привет", "rus"),
        detected("hello once more", "eng"),
    )
    texts = [cloud_transcriber.transcribe(SEGMENT) for _ in range(3)]
    assert texts == ["hello", "hello again", "hello once more"]
    assert requested_languages(urlopen) == [None, None, "en", None, "en"]


def test_a_pinned_session_never_asks_again(monkeypatch):
    urlopen = stub_scribe_answers(monkeypatch, detected("こんにちは", "fra"))
    assert cloud_transcriber.transcribe(SEGMENT, "ja") == "こんにちは"
    assert requested_languages(urlopen) == ["ja"]


@pytest.mark.parametrize(
    "payload", [{"text": "hello"}, {"text": "hello", "language_code": None}]
)
def test_an_answer_without_a_language_is_accepted(monkeypatch, payload):
    urlopen = stub_scribe_answers(monkeypatch, payload)
    assert cloud_transcriber.transcribe(SEGMENT) == "hello"
    assert requested_languages(urlopen) == [None]


def test_a_failed_pinned_retry_falls_back_to_hex(monkeypatch):
    urlopen = stub_scribe_answers(
        monkeypatch,
        detected("Pour le seul public", "fra"),
        urllib.error.URLError("offline"),
    )
    local = Mock(return_value="pode ser público")
    monkeypatch.setattr(transcriber, "transcribe", local)
    assert cloud_transcriber.transcribe_with_local_fallback(SEGMENT) == (
        "pode ser público"
    )
    local.assert_called_once_with(SEGMENT, None)
    assert requested_languages(urlopen) == [None, "pt"]


def test_a_pinned_retry_is_reported_with_what_scribe_detected(monkeypatch, capsys):
    stub_scribe_answers(
        monkeypatch,
        detected("Pour le seul public", "fra", 0.61),
        detected("pode ser público", "por"),
    )
    cloud_transcriber.transcribe(SEGMENT)
    report = capsys.readouterr().err
    assert "fra" in report
    assert "0.61" in report
    assert "pt" in report


@NO_FIXTURE_CHECK
@given(code=DETECTED_CODES)
def test_scribe_is_asked_once_for_a_spoken_or_absent_language_and_otherwise_twice(
    monkeypatch, code
):
    first = {"text": "first"} if code is None else detected("first", code)
    urlopen = stub_scribe_answers(
        monkeypatch, first, detected("second", "por"), detected("third", "por")
    )
    asked_once = code is None or code in SPOKEN_CODES
    text = cloud_transcriber.transcribe(SEGMENT)
    assert urlopen.call_count == (1 if asked_once else 2)
    assert text == ("first" if asked_once else "second")
