"""The two HTTP shapes the media providers need, on the standard library alone.

A provider refusal is not an error to trace out; it is something the agent will
paraphrase into the channel, so it comes back as one readable sentence.
"""

import json
import urllib.error
import urllib.request
import uuid

from agent_media_workspace import MediaRequestRefused

REQUEST_TIMEOUT_SECONDS = 180


def post_json(url, headers, body):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={**headers, "content-type": "application/json"},
    )
    return read_response(request)


def post_multipart(url, headers, fields, files):
    boundary = f"----clawde{uuid.uuid4().hex}"
    parts = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    for name, file_path in files:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{file_path.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n".encode()
        )
        parts.append(file_path.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        url,
        data=b"".join(parts),
        headers={
            **headers,
            "content-type": f"multipart/form-data; boundary={boundary}",
        },
    )
    return read_response(request)


def read_response(request):
    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            return json.load(response)
    except urllib.error.HTTPError as failure:
        raise MediaRequestRefused(describe_refusal(failure)) from None
    except OSError as failure:
        raise MediaRequestRefused(
            f"the media provider is unreachable: {failure}"
        ) from None


def describe_refusal(failure):
    try:
        reported = json.loads(failure.read().decode("utf-8"))
    except (ValueError, OSError):
        return f"the media provider refused this: HTTP {failure.code}"
    message = reported.get("error", {})
    if isinstance(message, dict):
        message = message.get("message", "")
    return f"the media provider refused this: {message or failure.code}"
