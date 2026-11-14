import functools
import json
import math
import os
import re
import sys
import urllib.request
import uuid
from pathlib import Path

from transcription import ordinary_words, transcriber

SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"
SCRIBE_MODEL = "scribe_v2"
API_KEY_FILE = Path.home() / ".secrets" / "elevenlabs-api-key"
REQUEST_TIMEOUT_SECONDS = 15
KEYTERMS_BEFORE_MINIMUM_BILLING = 100
ROSTER_SEPARATOR = " | "
PARENTHESIZED = re.compile(r"\s*\([^)]*\)")
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


@functools.cache
def servant_names(roster_path):
    try:
        lines = Path(roster_path).read_text().splitlines()
    except (OSError, ValueError):
        return ()
    names = (
        PARENTHESIZED.sub("", line.split(ROSTER_SEPARATOR)[0]).strip() for line in lines
    )
    return tuple(dict.fromkeys(name for name in names if name))


def familiarity(name, frequency_ranks):
    ranks = [frequency_ranks.get(ordinary_words.folded(word)) for word in name.split()]
    if None in ranks:
        return -math.inf
    return -max(ranks)


def recognized_terms():
    roster_path = os.environ.get("AVATAR_SERVANT_ROSTER")
    if not roster_path:
        return RECOGNIZED_TERMS
    frequency_ranks = ordinary_words.frequency_ranks() or {}
    names = [
        name for name in servant_names(roster_path) if name not in RECOGNIZED_TERMS
    ]
    names.sort(key=lambda name: familiarity(name, frequency_ranks))
    return RECOGNIZED_TERMS + tuple(
        names[: KEYTERMS_BEFORE_MINIMUM_BILLING - len(RECOGNIZED_TERMS)]
    )


def scribe_fields(language):
    fields = [("model_id", SCRIBE_MODEL), ("tag_audio_events", "false")]
    if language:
        fields.append(("language_code", language))
    return fields + [("keyterms", term) for term in recognized_terms()]


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
