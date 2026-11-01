import http.client
import io
import json
import re
import uuid
import wave

from speech_segmenter import SAMPLE_RATE

TRANSCRIBER_HOST = "127.0.0.1"
TRANSCRIBER_PORT = 8767
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


def multipart_field(boundary, name, value):
    return (
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
        f"\r\n\r\n{value}\r\n"
    )


def multipart_body(boundary, audio, language=None, prompt=None):
    optional_fields = {"language": language, "prompt": prompt}
    optional_parts = "".join(
        multipart_field(boundary, name, value)
        for name, value in optional_fields.items()
        if value
    )
    return (
        (
            multipart_field(boundary, "response_format", "json")
            + optional_parts
            + f"--{boundary}\r\nContent-Disposition: form-data; "
            f'name="file"; filename="segment.wav"\r\nContent-Type: audio/wav\r\n\r\n'
        ).encode()
        + audio
        + f"\r\n--{boundary}--\r\n".encode()
    )


def transcribe(pcm, language=None, prompt=None):
    boundary = uuid.uuid4().hex
    connection = http.client.HTTPConnection(
        TRANSCRIBER_HOST, TRANSCRIBER_PORT, timeout=REQUEST_TIMEOUT_SECONDS
    )
    try:
        connection.request(
            "POST",
            "/inference",
            body=multipart_body(boundary, wav_bytes(pcm), language, prompt),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        return clean_transcript(json.load(connection.getresponse()).get("text", ""))
    finally:
        connection.close()
