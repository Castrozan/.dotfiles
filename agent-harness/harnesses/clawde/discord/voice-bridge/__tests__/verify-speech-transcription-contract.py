import sys

import cloud_transcriber
from voice_bridge.speech_transcription import (
    DISCORD_CHANNEL_COUNT,
    DISCORD_SAMPLE_RATE,
    LISTENER_LANGUAGE,
    transcribe_discord_audio,
)

ONE_SECOND_OF_DISCORD_SILENCE = bytes(DISCORD_SAMPLE_RATE * DISCORD_CHANNEL_COUNT * 2)


def test_transcribes_discord_audio_through_the_avatar_cloud_transcriber():
    received_languages = []

    def transcribe_through_scribe(pcm, language=None):
        received_languages.append(language)
        return "oi" if pcm else ""

    cloud_transcriber.transcribe = transcribe_through_scribe
    transcript = transcribe_discord_audio(sys.argv[1], ONE_SECOND_OF_DISCORD_SILENCE)
    assert transcript == "oi"
    assert received_languages == [LISTENER_LANGUAGE]


test_transcribes_discord_audio_through_the_avatar_cloud_transcriber()
