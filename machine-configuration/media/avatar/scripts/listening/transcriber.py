import io
import json
import re
import urllib.request
import uuid
import wave

from speech_segmenter import SAMPLE_RATE

INFERENCE_URL = "http://127.0.0.1:8767/inference"
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


def multipart_body(boundary, audio):
    return (
        f'--{boundary}\r\nContent-Disposition: form-data; name="response_format"'
        f"\r\n\r\njson\r\n--{boundary}\r\nContent-Disposition: form-data; "
        f'name="file"; filename="segment.wav"\r\nContent-Type: audio/wav\r\n\r\n'
    ).encode() + audio + f"\r\n--{boundary}--\r\n".encode()


def transcribe(pcm):
    boundary = uuid.uuid4().hex
    request = urllib.request.Request(
        INFERENCE_URL,
        data=multipart_body(boundary, wav_bytes(pcm)),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return clean_transcript(json.load(response).get("text", ""))
