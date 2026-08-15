"""Speak one line into a WAV file in the calling agent's workspace and print its path.

Discord renders an attached WAV with a player, so a voice note is the same
outbound call as any other attachment. The provider answers with headerless PCM,
which is why the container is written here rather than shelled out to a codec.
"""

import argparse
import base64
import io
import sys
import wave
from datetime import date
from pathlib import Path

from agent_media_transport import post_json
from agent_media_workspace import (
    MediaRequestRefused,
    claim_daily_allowance,
    flatten_prompt,
    read_api_key,
    resolve_media_directory,
    write_media_file,
)

SPEECH_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-preview-tts:generateContent"
)
SECRET_NAME = "gemini-api-key"
VOICES = ("Leda", "Kore", "Aoede", "Zephyr", "Autonoe", "Puck", "Charon", "Fenrir")
DEFAULT_VOICE = "Leda"
TEXT_LENGTH_LIMIT = 600
DELIVERY_LENGTH_LIMIT = 200
DAILY_LIMIT = 40
SAMPLE_RATE_FALLBACK = 24000
SAMPLE_WIDTH_BYTES = 2


def parse_command_line_arguments(argv):
    parser = argparse.ArgumentParser(
        prog="clawde-agent-voice-note",
        description="Record one spoken line into this agent's own media directory.",
    )
    parser.add_argument(
        "--text", required=True, help="What to say, in any language the voice speaks."
    )
    parser.add_argument(
        "--delivery",
        default="",
        help='How to say it, e.g. "irritada e arrastada". Steers tone, is never spoken aloud.',
    )
    parser.add_argument("--voice", choices=VOICES, default=DEFAULT_VOICE)
    return parser.parse_args(argv)


def compose_speech_prompt(text, delivery):
    spoken = flatten_prompt(text, TEXT_LENGTH_LIMIT)
    if not delivery.strip():
        return spoken
    return f"{flatten_prompt(delivery, DELIVERY_LENGTH_LIMIT)}: {spoken}"


def request_speech(api_key, speech_prompt, voice):
    return post_json(
        SPEECH_URL,
        {"x-goog-api-key": api_key},
        {
            "contents": [{"parts": [{"text": speech_prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
                },
            },
        },
    )


def decode_speech(reported):
    for candidate in reported.get("candidates") or []:
        for part in candidate.get("content", {}).get("parts") or []:
            inline = part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"]), sample_rate_of(
                    inline.get("mimeType", "")
                )
    raise MediaRequestRefused("the speech provider returned no audio")


def sample_rate_of(mime_type):
    for parameter in mime_type.split(";"):
        name, _, value = parameter.strip().partition("=")
        if name == "rate" and value.isdigit():
            return int(value)
    return SAMPLE_RATE_FALLBACK


def wrap_as_wave(pcm, sample_rate):
    wave_bytes = io.BytesIO()
    with wave.open(wave_bytes, "wb") as container:
        container.setnchannels(1)
        container.setsampwidth(SAMPLE_WIDTH_BYTES)
        container.setframerate(sample_rate)
        container.writeframes(pcm)
    return wave_bytes.getvalue()


def generate_agent_voice_note(working_directory, arguments, today):
    media_directory = resolve_media_directory(working_directory)
    speech_prompt = compose_speech_prompt(arguments.text, arguments.delivery)
    api_key = read_api_key(SECRET_NAME)
    claim_daily_allowance(media_directory, "voice", DAILY_LIMIT, today)
    pcm, sample_rate = decode_speech(
        request_speech(api_key, speech_prompt, arguments.voice)
    )
    return write_media_file(
        media_directory, "voice", ".wav", wrap_as_wave(pcm, sample_rate)
    )


def main(argv=None):
    arguments = parse_command_line_arguments(sys.argv[1:] if argv is None else argv)
    try:
        media_file = generate_agent_voice_note(Path.cwd(), arguments, date.today())
    except MediaRequestRefused as refusal:
        print(str(refusal), file=sys.stderr)
        return 1
    print(media_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
