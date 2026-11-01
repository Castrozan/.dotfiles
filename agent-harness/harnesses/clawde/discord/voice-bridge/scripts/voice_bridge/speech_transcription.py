import subprocess

from transcriber import transcribe

DISCORD_SAMPLE_RATE = 48000
DISCORD_CHANNEL_COUNT = 2
WHISPER_SAMPLE_RATE = 16000
DOWNMIX_TIMEOUT_SECONDS = 10


def downmix_discord_audio(ffmpeg_executable, pcm):
    return subprocess.run(
        [
            ffmpeg_executable,
            "-loglevel",
            "error",
            "-f",
            "s16le",
            "-ar",
            str(DISCORD_SAMPLE_RATE),
            "-ac",
            str(DISCORD_CHANNEL_COUNT),
            "-i",
            "pipe:0",
            "-f",
            "s16le",
            "-ar",
            str(WHISPER_SAMPLE_RATE),
            "-ac",
            "1",
            "pipe:1",
        ],
        input=pcm,
        capture_output=True,
        check=True,
        timeout=DOWNMIX_TIMEOUT_SECONDS,
    ).stdout


def transcribe_discord_audio(ffmpeg_executable, pcm):
    return transcribe(downmix_discord_audio(ffmpeg_executable, pcm))
