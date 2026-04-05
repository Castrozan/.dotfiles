#!/usr/bin/env python3

import json
import sys
from urllib.parse import urlparse

TWITTER_HOSTS = {
    "x.com",
    "twitter.com",
    "www.x.com",
    "www.twitter.com",
    "mobile.twitter.com",
}

REDIRECT_MESSAGE = (
    "BLOCKED: x.com/twitter.com URLs cannot be fetched with WebFetch or browser tools. "
    "Use the fxtwitter API instead: "
    "curl -sL 'https://api.fxtwitter.com/{user}/status/{tweet_id}' "
    "Extract user and tweet_id from the URL. Returns JSON with tweet text, media URLs, "
    "and engagement metrics. Download media with curl -sL -o /tmp/file.ext '{media_url}'. "
    "For advanced operations (posting, searching, profiles), invoke Skill(skill='comms')."
)


def extract_url_from_tool_input(tool_input):
    for key in ("url", "uri"):
        value = tool_input.get(key, "")
        if value:
            return value
    return ""


def is_twitter_url(url):
    try:
        parsed = urlparse(url)
        return parsed.hostname in TWITTER_HOSTS
    except Exception:
        return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    url = extract_url_from_tool_input(tool_input)

    if not url or not is_twitter_url(url):
        sys.exit(0)

    print(REDIRECT_MESSAGE, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
