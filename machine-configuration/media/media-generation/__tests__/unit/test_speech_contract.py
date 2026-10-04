import pytest

from media_speech.contract import (
    CharacterAlignment,
    SpeechError,
    SpeechRequest,
    SynthesizedSpeech,
)
from media_speech.service import SpeechService
from media_speech_cli import main


@pytest.mark.parametrize("text", ["", " \n", "a" * 4001, "abc\x00def"])
def test_invalid_text_never_reaches_a_provider(text):
    with pytest.raises(SpeechError, match="invalid_text"):
        SpeechRequest(text, "pf_dora", "pt-br")


@pytest.mark.parametrize("voice", ["", "../voice", "voice?id=1", "voz-á"])
def test_invalid_voice_cannot_enter_a_provider_path(voice):
    with pytest.raises(SpeechError, match="invalid_voice"):
        SpeechRequest("Hello", voice, "en-us")


@pytest.mark.parametrize(
    "speech",
    [
        SynthesizedSpeech(b"", 24000),
        SynthesizedSpeech(b"odd", 24000),
        SynthesizedSpeech(b"\x00\x01", 44100),
    ],
)
def test_invalid_audio_never_becomes_a_success(
    tmp_path, speech_request, operation_id, speech, provider_factory
):
    service = SpeechService(tmp_path)
    with pytest.raises(SpeechError):
        service.generate(operation_id, speech_request, provider_factory(speech))
    assert service.inspect(operation_id)["status"] == "failed"
    assert not (tmp_path / operation_id / "speech.wav").exists()


@pytest.mark.parametrize(
    "alignment",
    [
        CharacterAlignment(("a",), (), (0.1,)),
        CharacterAlignment(("a",), (float("nan"),), (0.1,)),
        CharacterAlignment(("a",), (0.2,), (0.1,)),
        CharacterAlignment(("a",), (0,), (2,)),
    ],
)
def test_invalid_alignment_never_becomes_caption_evidence(
    tmp_path, speech_request, operation_id, alignment, provider_factory
):
    service = SpeechService(tmp_path)
    speech = SynthesizedSpeech(b"\x00\x01" * 24000, 24000, alignment)
    with pytest.raises(SpeechError, match="invalid_alignment"):
        service.generate(operation_id, speech_request, provider_factory(speech))


def test_missing_cloud_credentials_fail_before_dispatch(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert (
        main(
            [
                "--state-directory",
                str(tmp_path),
                "generate",
                "--provider",
                "elevenlabs",
                "--voice",
                "voice",
                "--language",
                "en-us",
                "--text",
                "Hello",
            ]
        )
        == 1
    )
    assert "missing_credentials" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_operation_id_cannot_escape_state_directory(tmp_path):
    with pytest.raises(SpeechError, match="invalid_operation_id"):
        SpeechService(tmp_path).inspect("../outside")
