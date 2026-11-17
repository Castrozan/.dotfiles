import json
import wave

import mac_speech
import pytest

CHARACTERS = [
    {"name": "first-of-the-cast", "cloudVoice": "voice-of-the-first"},
    {"name": "swordsman", "cloudVoice": "voice-of-the-swordsman"},
]
DELIVERY = {"happy": "warm and cheerful, smiling"}


@pytest.fixture(autouse=True)
def declared_cast(monkeypatch, tmp_path):
    voices = tmp_path / "voices.json"
    voices.write_text(json.dumps(CHARACTERS))
    delivery = tmp_path / "delivery.json"
    delivery.write_text(json.dumps(DELIVERY))
    servants = tmp_path / "servants.txt"
    servants.write_text("Sasaki Kojirou | swordsman\nNobody Cast | not-in-the-cast\n")
    monkeypatch.setenv(mac_speech.VOICES_ENVIRONMENT_VARIABLE, str(voices))
    monkeypatch.setenv(mac_speech.DELIVERY_ENVIRONMENT_VARIABLE, str(delivery))
    monkeypatch.setenv("AVATAR_SERVANT_CHARACTERS", str(servants))


def test_a_servant_speaks_in_the_voice_of_its_character():
    assert mac_speech.voice_of("Sasaki Kojirou") == "voice-of-the-swordsman"


@pytest.mark.parametrize("servant", [None, "Unlisted Servant", "Nobody Cast"])
def test_anyone_without_a_voiced_character_speaks_in_the_first_voice(servant):
    assert mac_speech.voice_of(servant) == "voice-of-the-first"


@pytest.mark.parametrize(
    ("emotion", "delivery"),
    [("happy", DELIVERY["happy"]), ("neutral", mac_speech.NATURAL_DELIVERY)],
)
def test_the_emotion_becomes_the_delivery_the_voice_is_directed_with(emotion, delivery):
    command = mac_speech.synthesis_command("Good evening", emotion, "a-voice")
    assert command[command.index("--directions") + 1] == delivery
    assert command[command.index("--voice") + 1] == "a-voice"
    assert command[command.index("--text") + 1] == "Good evening"


def test_the_samples_of_a_recording_are_its_audio_without_the_header(tmp_path):
    samples = b"\x01\x02" * 240
    recording = tmp_path / "speech.wav"
    with wave.open(str(recording), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(samples)
    assert mac_speech.samples_of(str(recording)) == samples
