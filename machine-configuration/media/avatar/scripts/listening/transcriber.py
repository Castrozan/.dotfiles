import http.client
import io
import json
import re
import urllib.parse
import wave
from pathlib import Path

from speech_segmenter import SAMPLE_RATE

HEX_DISCOVERY_FILE = Path.home() / ".local/share/hex/local-api.json"
HEX_HOST = "127.0.0.1"
HEX_MODEL = "parakeet_v3"
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


def transcription_path(language):
    selection = {"model": HEX_MODEL} | ({"language": language} if language else {})
    return f"/transcriptions?{urllib.parse.urlencode(selection)}"


def transcribe(pcm, language=None):
    discovery = json.loads(HEX_DISCOVERY_FILE.read_text())
    connection = http.client.HTTPConnection(
        HEX_HOST, discovery["port"], timeout=REQUEST_TIMEOUT_SECONDS
    )
    try:
        connection.request(
            "POST",
            transcription_path(language),
            body=wav_bytes(pcm),
            headers={
                "Authorization": f"Bearer {discovery['token']}",
                "Content-Type": "audio/wav",
            },
        )
        response = connection.getresponse()
        answer = json.load(response)
        if response.status != 200:
            raise ConnectionError(f"Hex refused the segment: {answer.get('code')}")
        return clean_transcript(answer["transcript"])
    finally:
        connection.close()
