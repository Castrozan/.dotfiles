from pathlib import Path

import media_speech_cli
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
    provider = provider_factory(speech)
    with pytest.raises(SpeechError):
        service.generate(operation_id, speech_request, provider)
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
    provider = provider_factory(speech)
    with pytest.raises(SpeechError, match="invalid_alignment"):
        service.generate(operation_id, speech_request, provider)


def test_missing_cloud_credentials_fail_before_dispatch(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
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


@pytest.mark.parametrize("environment_key", [None, "explicit-environment-key"])
def test_cloud_cli_loads_credentials_without_disclosing_them(
    tmp_path, monkeypatch, capsys, provider_factory, environment_key
):
    credential_directory = tmp_path / ".secrets"
    credential_directory.mkdir()
    (credential_directory / "elevenlabs-api-key").write_text("deployed-file-key\n")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    if environment_key:
        monkeypatch.setenv("ELEVENLABS_API_KEY", environment_key)
    expected_key = environment_key or "deployed-file-key"

    def create_provider(api_key):
        assert api_key == expected_key
        return provider_factory()

    monkeypatch.setattr(media_speech_cli, "ElevenLabsSpeechProvider", create_provider)
    assert (
        main(
            [
                "--state-directory",
                str(tmp_path / "operations"),
                "generate",
                "--provider",
                "elevenlabs",
                "--voice",
                "voice",
                "--language",
                "pt-br",
                "--text",
                "Olá, Lucas.",
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert expected_key not in output.out + output.err
    assert '"status": "succeeded"' in output.out


def test_empty_deployed_credentials_fail_before_dispatch(tmp_path, monkeypatch, capsys):
    credential_directory = tmp_path / ".secrets"
    credential_directory.mkdir()
    (credential_directory / "elevenlabs-api-key").write_text(" \n")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert (
        main(
            [
                "--state-directory",
                str(tmp_path / "operations"),
                "generate",
                "--provider",
                "elevenlabs",
                "--voice",
                "voice",
                "--language",
                "pt-br",
                "--text",
                "Olá, Lucas.",
            ]
        )
        == 1
    )
    assert "missing_credentials" in capsys.readouterr().err
    assert not (tmp_path / "operations").exists()


def test_operation_id_cannot_escape_state_directory(tmp_path):
    service = SpeechService(tmp_path)
    with pytest.raises(SpeechError, match="invalid_operation_id"):
        service.inspect("../outside")
