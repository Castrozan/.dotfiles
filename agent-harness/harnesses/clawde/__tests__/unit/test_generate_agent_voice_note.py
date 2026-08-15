import base64
import wave
from datetime import date

import generate_agent_voice_note
import pytest
from agent_media_workspace import MediaRequestRefused

TODAY = date(2026, 8, 15)
PCM_SILENCE = b"\x00\x01" * 240


def spoken_answer(sample_rate=24000):
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": f"audio/L16;codec=pcm;rate={sample_rate}",
                                "data": base64.b64encode(PCM_SILENCE).decode(),
                            }
                        }
                    ]
                }
            }
        ]
    }


def stub_provider(monkeypatch, recorder, reported=None):
    answered = spoken_answer() if reported is None else reported

    def answer(*call, **_):
        recorder.append(call)
        return answered

    monkeypatch.setattr(generate_agent_voice_note, "post_json", answer)


def voice_arguments(**overrides):
    flags = [item for pair in overrides.items() for item in pair]
    return generate_agent_voice_note.parse_command_line_arguments(
        ["--text", "some daqui, verme", *flags]
    )


def speak(workspace, **overrides):
    return generate_agent_voice_note.generate_agent_voice_note(
        workspace, voice_arguments(**overrides), TODAY
    )


def test_a_voice_note_is_written_as_a_playable_wave(media_agent_workspace, monkeypatch):
    stub_provider(monkeypatch, [])

    media_file = speak(media_agent_workspace)

    with wave.open(str(media_file), "rb") as container:
        assert container.getnchannels() == 1
        assert container.getsampwidth() == 2
        assert container.getframerate() == 24000
        assert container.readframes(container.getnframes()) == PCM_SILENCE


def test_the_delivery_note_steers_the_line_without_being_spoken(
    media_agent_workspace, monkeypatch
):
    calls = []
    stub_provider(monkeypatch, calls)

    speak(media_agent_workspace, **{"--delivery": "irritada e arrastada"})

    assert calls[0][2]["contents"][0]["parts"][0]["text"] == (
        "irritada e arrastada: some daqui, verme"
    )


def test_the_chosen_voice_reaches_the_provider(media_agent_workspace, monkeypatch):
    calls = []
    stub_provider(monkeypatch, calls)

    speak(media_agent_workspace, **{"--voice": "Kore"})

    speech_config = calls[0][2]["generationConfig"]["speechConfig"]
    assert speech_config["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"] == "Kore"


def test_the_container_follows_the_rate_the_provider_reports(
    media_agent_workspace, monkeypatch
):
    stub_provider(monkeypatch, [], reported=spoken_answer(sample_rate=16000))

    with wave.open(str(speak(media_agent_workspace)), "rb") as container:
        assert container.getframerate() == 16000


def test_a_provider_answering_with_no_audio_is_reported(
    media_agent_workspace, monkeypatch
):
    stub_provider(monkeypatch, [], reported={"candidates": []})

    with pytest.raises(MediaRequestRefused, match="no audio"):
        speak(media_agent_workspace)


def test_an_oversized_line_is_refused_before_the_provider_is_called(
    media_agent_workspace, monkeypatch
):
    calls = []
    stub_provider(monkeypatch, calls)

    with pytest.raises(MediaRequestRefused, match="keep it under"):
        generate_agent_voice_note.generate_agent_voice_note(
            media_agent_workspace,
            generate_agent_voice_note.parse_command_line_arguments(
                ["--text", "a " * 400]
            ),
            TODAY,
        )

    assert calls == []
