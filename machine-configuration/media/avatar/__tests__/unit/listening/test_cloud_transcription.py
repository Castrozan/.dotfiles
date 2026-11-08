import io
import json
import urllib.error
from unittest.mock import MagicMock, Mock

import cloud_transcriber
import transcriber


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
