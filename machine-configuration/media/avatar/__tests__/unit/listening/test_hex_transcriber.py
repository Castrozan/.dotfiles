import json
import struct
from pathlib import Path
from unittest.mock import Mock

import pytest

from transcription import transcriber

FRAME_SAMPLES = 480


def frame(amplitude):
    return struct.pack(f"<{FRAME_SAMPLES}h", *([amplitude] * FRAME_SAMPLES))


INSTALLED_PREFERRED = [
    {"id": "parakeet_unified_en", "installed": True},
    {"id": "parakeet_v3", "installed": True},
]


def stub_hex(monkeypatch, tmp_path, status, payload, models=INSTALLED_PREFERRED):
    discovery = tmp_path / "local-api.json"
    discovery.write_text(json.dumps({"port": 42267, "token": "secret"}))
    monkeypatch.setattr(transcriber, "HEX_DISCOVERY_FILE", discovery)
    listing = Mock(status=200)
    listing.read.return_value = json.dumps(models).encode()
    response = Mock(status=status)
    response.read.return_value = json.dumps(payload).encode()
    connection = Mock()
    connection.getresponse.side_effect = [listing, response]
    monkeypatch.setattr(
        transcriber.http.client, "HTTPConnection", Mock(return_value=connection)
    )
    return connection


def test_transcribe_posts_the_segment_to_hex_and_returns_the_cleaned_text(
    monkeypatch, tmp_path
):
    connection = stub_hex(monkeypatch, tmp_path, 200, {"transcript": " bom  dia "})
    assert transcriber.transcribe(frame(1000), "pt") == "bom dia"
    assert connection.request.call_args.args == (
        "POST",
        "/transcriptions?model=parakeet_v3&language=pt",
    )
    headers = connection.request.call_args.kwargs["headers"]
    assert headers == {"Authorization": "Bearer secret", "Content-Type": "audio/wav"}
    assert connection.close.call_count == 2


def test_language_stays_automatic_unless_requested():
    assert (
        transcriber.transcription_path("parakeet_v3", None)
        == "/transcriptions?model=parakeet_v3"
    )


def test_a_machine_without_the_preferred_model_uses_one_it_has(monkeypatch, tmp_path):
    only_english = [
        {"id": "parakeet_v3", "installed": False},
        {"id": "parakeet_unified_en", "installed": True},
    ]
    connection = stub_hex(
        monkeypatch, tmp_path, 200, {"transcript": "hey"}, only_english
    )
    assert transcriber.transcribe(frame(1000)) == "hey"
    assert connection.request.call_args.args == (
        "POST",
        "/transcriptions?model=parakeet_unified_en",
    )


def test_hex_with_no_model_installed_is_a_connection_failure(monkeypatch, tmp_path):
    none_installed = [{"id": "parakeet_v3", "installed": False}]
    stub_hex(monkeypatch, tmp_path, 200, {"transcript": "hey"}, none_installed)
    with pytest.raises(OSError, match="no transcription model"):
        transcriber.transcribe(frame(1000))


@pytest.mark.parametrize(
    ("platform", "directory"),
    [
        ("darwin", "Library/Application Support/hex"),
        ("linux", ".local/share/hex"),
    ],
)
def test_hex_is_found_where_each_system_keeps_it(platform, directory):
    expected = Path.home() / directory / "local-api.json"
    assert transcriber.hex_discovery_file(platform) == expected


def test_a_refused_segment_is_retried_as_a_connection_failure(monkeypatch, tmp_path):
    stub_hex(monkeypatch, tmp_path, 429, {"code": "queue-full"})
    with pytest.raises(OSError, match="queue-full"):
        transcriber.transcribe(frame(1000))
