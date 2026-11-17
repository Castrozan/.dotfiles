import json
import os
import pathlib
import subprocess
import wave

import servant_character

MODEL = "eleven_v4"
LANGUAGE = "pt-br"
NATURAL_DELIVERY = "natural and conversational"
VOICES_ENVIRONMENT_VARIABLE = "AVATAR_CHARACTER_VOICES"
DELIVERY_ENVIRONMENT_VARIABLE = "AVATAR_EMOTION_DELIVERY"
SYNTHESIS_TIMEOUT_SECONDS = 30
PLAYBACK_TIMEOUT_SECONDS = 310
PLAYER = "/usr/bin/afplay"


def declared(environment_variable):
    return json.loads(pathlib.Path(os.environ[environment_variable]).read_text())


def voice_of(servant):
    characters = declared(VOICES_ENVIRONMENT_VARIABLE)
    chosen = servant_character.character_for(servant)
    voices = {character["name"]: character["cloudVoice"] for character in characters}
    return voices.get(chosen, characters[0]["cloudVoice"])


def delivery_of(emotion):
    return declared(DELIVERY_ENVIRONMENT_VARIABLE).get(emotion, NATURAL_DELIVERY)


def synthesis_command(text, emotion, voice):
    return [
        "media-speech",
        "generate",
        "--provider",
        "elevenlabs",
        "--model",
        MODEL,
        "--directions",
        delivery_of(emotion),
        "--language",
        LANGUAGE,
        "--voice",
        voice,
        "--text",
        text,
    ]


def synthesized(text, emotion, voice):
    generated = subprocess.run(
        synthesis_command(text, emotion, voice),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=SYNTHESIS_TIMEOUT_SECONDS,
    )
    return json.loads(generated.stdout)["audio"]["path"]


def samples_of(recording):
    with wave.open(recording, "rb") as audio:
        return audio.readframes(audio.getnframes())


def play_without_a_seat(recording):
    subprocess.run([PLAYER, recording], check=True, timeout=PLAYBACK_TIMEOUT_SECONDS)
