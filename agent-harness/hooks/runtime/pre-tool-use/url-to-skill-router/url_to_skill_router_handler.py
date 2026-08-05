from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402

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
    "For advanced operations (posting, searching, profiles), invoke Skill(skill='twitter') "
    "for Twitter-specific workflows."
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


def handle(hook_input):
    tool_input = hook_input.get("tool_input", {}) or {}
    url = extract_url_from_tool_input(tool_input)
    if not url or not is_twitter_url(url):
        return None
    return HandlerResult(decision="deny", reason=REDIRECT_MESSAGE)
