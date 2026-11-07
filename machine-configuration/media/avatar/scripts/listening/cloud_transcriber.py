import json
import os
import sys
import urllib.request
import uuid
from pathlib import Path

import transcriber

SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"
SCRIBE_MODEL = "scribe_v2"
API_KEY_FILE = Path.home() / ".secrets" / "elevenlabs-api-key"
REQUEST_TIMEOUT_SECONDS = 15
RECOGNIZED_TERMS = (
    "ElevenLabs",
    "Hex",
    "NixOS",
    "chise",
    "Claude",
    "Hyprland",
    "dotfiles",
    "rebuild",
    "Lucas",
    "Lulu",
)


def api_key():
    return os.environ.get("ELEVENLABS_API_KEY") or API_KEY_FILE.read_text().strip()


def scribe_fields(language):
    fields = [("model_id", SCRIBE_MODEL), ("tag_audio_events", "false")]
    if language:
        fields.append(("language_code", language))
    return fields + [("keyterms", term) for term in RECOGNIZED_TERMS]


def multipart_body(boundary, fields, wav):
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
        f"{value}\r\n".encode()
        for name, value in fields
    ]
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="segment.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
        + wav
        + f"\r\n--{boundary}--\r\n".encode()
    )
    return b"".join(parts)


def transcribe(pcm, language=None):
    boundary = uuid.uuid4().hex
    request = urllib.request.Request(
        SCRIBE_URL,
        data=multipart_body(
            boundary, scribe_fields(language), transcriber.wav_bytes(pcm)
        ),
        headers={
            "xi-api-key": api_key(),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return transcriber.clean_transcript(json.load(response)["text"])


def transcribe_with_local_fallback(pcm, language=None):
    try:
        return transcribe(pcm, language)
    except (OSError, ValueError, KeyError) as error:
        print(f"Cloud transcription failed, using Hex: {error}", file=sys.stderr)
        return transcriber.transcribe(pcm, language)
