import io
import json
import re
import urllib.error
from unittest.mock import MagicMock, Mock

import pytest

from transcription import cloud_transcriber
from transcription import transcriber
from transcription.ordinary_words import folded
from wake_phrase import spoken_name


@pytest.fixture(autouse=True)
def fresh_roster_cache(monkeypatch):
    monkeypatch.delenv("AVATAR_SERVANT_ROSTER", raising=False)
    monkeypatch.delenv("AVATAR_ORDINARY_WORDS", raising=False)
    cloud_transcriber.servant_names.cache_clear()
    yield
    cloud_transcriber.servant_names.cache_clear()


def stub_scribe(monkeypatch, payload):
    response = MagicMock()
    response.__enter__.return_value = io.BytesIO(json.dumps(payload).encode())
    urlopen = Mock(return_value=response)
    monkeypatch.setattr(cloud_transcriber.urllib.request, "urlopen", urlopen)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    return urlopen


def test_a_segment_is_sent_to_scribe_with_the_pinned_language(monkeypatch):
    urlopen = stub_scribe(monkeypatch, {"text": " bom  dia "})
    assert cloud_transcriber.transcribe(b"\x00\x00" * 1600, "pt") == "bom dia"
    request = urlopen.call_args.args[0]
    assert request.full_url == cloud_transcriber.SCRIBE_URL
    assert request.get_header("Xi-api-key") == "test-key"
    assert b'name="language_code"\r\n\r\npt\r\n' in request.data
    assert b'name="model_id"\r\n\r\nscribe_v2\r\n' in request.data
    assert b"RIFF" in request.data


def test_every_recognized_term_is_its_own_keyterm_field(monkeypatch):
    urlopen = stub_scribe(monkeypatch, {"text": "Hex"})
    cloud_transcriber.transcribe(b"\x00\x00" * 1600, "pt")
    data = urlopen.call_args.args[0].data
    assert data.count(b'name="keyterms"') == len(cloud_transcriber.RECOGNIZED_TERMS)
    assert b'name="keyterms"\r\n\r\nElevenLabs\r\n' in data


def keyterms_sent(urlopen):
    data = urlopen.call_args.args[0].data.decode(errors="replace")
    return re.findall(r'name="keyterms"\r\n\r\n(.*?)\r\n', data)


def test_the_called_names_follow_the_fixed_terms_without_repeats(monkeypatch, tmp_path):
    roster = tmp_path / "roster.txt"
    roster.write_text(
        "Medea | witch\nRobin Hood | archer\nMedea | other\n"
        "Altria Pendragon (Lancer) | lancer\nAltria Pendragon | saber\nHex | x\n"
    )
    monkeypatch.setenv("AVATAR_SERVANT_ROSTER", str(roster))
    urlopen = stub_scribe(monkeypatch, {"text": "Hex"})
    cloud_transcriber.transcribe(b"\x00\x00" * 1600, "pt")
    fixed = list(cloud_transcriber.RECOGNIZED_TERMS)
    assert keyterms_sent(urlopen) == fixed + ["Medea", "Robin", "Altria"]


def test_a_servant_is_a_keyterm_by_the_name_the_wake_hears(monkeypatch, tmp_path):
    roster = tmp_path / "roster.txt"
    roster.write_text("Hassan-i-Sabbah | assassin\nSasaki Kojirou | samurai\n")
    monkeypatch.setenv("AVATAR_SERVANT_ROSTER", str(roster))
    terms = cloud_transcriber.recognized_terms()
    assert terms[len(cloud_transcriber.RECOGNIZED_TERMS) :] == ("Hassan", "Sasaki")
    assert {folded(term) for term in terms} >= {
        spoken_name("Hassan-i-Sabbah"),
        spoken_name("Sasaki Kojirou"),
    }


def test_the_least_familiar_names_are_kept_when_the_roster_is_long(
    monkeypatch, tmp_path
):
    words = tmp_path / "words.txt"
    words.write_text("david 900\nrobin 800\nhood 700\n")
    roster = tmp_path / "roster.txt"
    roster.write_text(
        "David | king\nRobin Hood | archer\n"
        + "".join(f"Servant{index} | x\n" for index in range(89))
    )
    monkeypatch.setenv("AVATAR_ORDINARY_WORDS", str(words))
    monkeypatch.setenv("AVATAR_SERVANT_ROSTER", str(roster))
    terms = cloud_transcriber.recognized_terms()
    assert len(terms) == cloud_transcriber.KEYTERMS_BEFORE_MINIMUM_BILLING
    assert "Robin" in terms
    assert "David" not in terms


def test_the_keyterms_never_pass_the_minimum_billing_threshold(monkeypatch, tmp_path):
    roster = tmp_path / "roster.txt"
    roster.write_text("".join(f"Servant{index} | x\n" for index in range(300)))
    monkeypatch.setenv("AVATAR_SERVANT_ROSTER", str(roster))
    urlopen = stub_scribe(monkeypatch, {"text": "Hex"})
    cloud_transcriber.transcribe(b"\x00\x00" * 1600, "pt")
    terms = keyterms_sent(urlopen)
    assert len(terms) == cloud_transcriber.KEYTERMS_BEFORE_MINIMUM_BILLING
    assert terms[: len(cloud_transcriber.RECOGNIZED_TERMS)] == list(
        cloud_transcriber.RECOGNIZED_TERMS
    )


def test_an_unreadable_roster_leaves_only_the_fixed_terms(monkeypatch, tmp_path):
    monkeypatch.setenv("AVATAR_SERVANT_ROSTER", str(tmp_path / "missing.txt"))
    urlopen = stub_scribe(monkeypatch, {"text": "Hex"})
    cloud_transcriber.transcribe(b"\x00\x00" * 1600, "pt")
    assert keyterms_sent(urlopen) == list(cloud_transcriber.RECOGNIZED_TERMS)


def test_the_roster_is_read_once_per_process(monkeypatch, tmp_path):
    roster = tmp_path / "roster.txt"
    roster.write_text("Medea | witch\n")
    monkeypatch.setenv("AVATAR_SERVANT_ROSTER", str(roster))
    assert cloud_transcriber.recognized_terms()[-1] == "Medea"
    roster.write_text("Circe | witch\n")
    assert cloud_transcriber.recognized_terms()[-1] == "Medea"


def test_language_stays_automatic_unless_requested(monkeypatch):
    urlopen = stub_scribe(monkeypatch, {"text": "hello"})
    cloud_transcriber.transcribe(b"\x00\x00" * 1600)
    assert b"language_code" not in urlopen.call_args.args[0].data


def test_a_failed_cloud_request_falls_back_to_hex(monkeypatch):
    monkeypatch.setattr(
        cloud_transcriber,
        "transcribe",
        Mock(side_effect=urllib.error.URLError("offline")),
    )
    local = Mock(return_value="oi")
    monkeypatch.setattr(transcriber, "transcribe", local)
    assert cloud_transcriber.transcribe_with_local_fallback(b"pcm", "pt") == "oi"
    local.assert_called_once_with(b"pcm", "pt")
