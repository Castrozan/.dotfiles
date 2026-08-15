"""The one HTTP shape the media providers need, on the standard library alone.

A provider refusal is not an error to trace out; it is something the agent will
paraphrase into the channel, so it comes back as one readable sentence.
"""

import json
import urllib.error
import urllib.request

from agent_media_workspace import MediaRequestRefused

REQUEST_TIMEOUT_SECONDS = 180
# Klipy answers 403 to the standard library's own user agent, so every request
# names the caller instead of hiding as a browser.
USER_AGENT = "clawde-agent-media/1.0"


def post_json(url, headers, body):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            **headers,
            "content-type": "application/json",
            "user-agent": USER_AGENT,
        },
    )
    return read_response(request)


def get_json(url):
    return read_response(
        urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    )


def fetch_bytes(url):
    """Media the provider hosts, pulled down so the agent can open it locally."""
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"user-agent": USER_AGENT}),
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            return response.read()
    except urllib.error.HTTPError as failure:
        raise MediaRequestRefused(describe_refusal(failure)) from None
    except OSError as failure:
        raise MediaRequestRefused(f"that media would not download: {failure}") from None


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
