import http.client
import io
import json
import re
import sys
import urllib.parse
import wave
from pathlib import Path

from speech_segmenter import SAMPLE_RATE

HEX_DATA_DIRECTORIES = {"darwin": "Library/Application Support/hex"}


def hex_discovery_file(platform):
    directory = HEX_DATA_DIRECTORIES.get(platform, ".local/share/hex")
    return Path.home() / directory / "local-api.json"


HEX_DISCOVERY_FILE = hex_discovery_file(sys.platform)
HEX_HOST = "127.0.0.1"
PREFERRED_MODEL = "parakeet_v3"
REQUEST_TIMEOUT_SECONDS = 60
NON_SPEECH_MARKER = re.compile(r"^\s*(\[[^\]]*\]|\([^)]*\)|\*[^*]*\*)?\s*$")


def clean_transcript(text):
    return "" if NON_SPEECH_MARKER.match(text) else " ".join(text.split())


def wav_bytes(pcm):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm)
    return buffer.getvalue()


def transcription_path(model, language):
    selection = {"model": model} | ({"language": language} if language else {})
    return f"/transcriptions?{urllib.parse.urlencode(selection)}"


def asked_of_hex(discovery, method, path, body=None):
    connection = http.client.HTTPConnection(
        HEX_HOST, discovery["port"], timeout=REQUEST_TIMEOUT_SECONDS
    )
    try:
        connection.request(
            method,
            path,
            body=body,
            headers={
                "Authorization": f"Bearer {discovery['token']}",
                "Content-Type": "audio/wav",
            },
        )
        response = connection.getresponse()
        return response.status, json.load(response)
    finally:
        connection.close()


def installed_model(models):
    installed = [model["id"] for model in models if model["installed"]]
    if PREFERRED_MODEL in installed:
        return PREFERRED_MODEL
    if not installed:
        raise ConnectionError("Hex has no transcription model installed")
    return installed[0]


def transcribe(pcm, language=None):
    discovery = json.loads(HEX_DISCOVERY_FILE.read_text())
    _, models = asked_of_hex(discovery, "GET", "/models")
    status, answer = asked_of_hex(
        discovery,
        "POST",
        transcription_path(installed_model(models), language),
        wav_bytes(pcm),
    )
    if status != 200:
        raise ConnectionError(f"Hex refused the segment: {answer.get('code')}")
    return clean_transcript(answer["transcript"])


def main():
    print(transcribe(sys.stdin.buffer.read()))


if __name__ == "__main__":
    main()
