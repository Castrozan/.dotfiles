"""Pull candidate GIFs down so the agent can look at them before sending one.

A search engine ranks by tags, not by whether the thing is actually funny in the
room it is about to land in. So this downloads a handful of candidates into the
agent's workspace and prints their paths: one small file to open and judge, one
send-quality file to attach once a candidate wins. Choosing is the agent's job
and stays out of this script.
"""

import argparse
import datetime
import sys
import urllib.parse

from agent_media_transport import fetch_bytes, get_json
from agent_media_workspace import (
    MediaRequestRefused,
    claim_daily_allowance,
    flatten_prompt,
    read_api_key,
    resolve_media_directory,
    write_media_file,
)

SEARCH_URL = "https://api.klipy.com/api/v1/{key}/gifs/search?q={query}"
TRENDING_URL = "https://api.klipy.com/api/v1/{key}/gifs/trending?"
SECRET_NAME = "klipy-api-key"
QUERY_LENGTH_LIMIT = 120
DEFAULT_COUNT = 3
MAX_COUNT = 6
DAILY_LIMIT = 60
PREVIEW_SIZE_LIMIT = 2 * 1024 * 1024
ATTACHMENT_SIZE_LIMIT = 12 * 1024 * 1024
TIER_ORDER = ("hd", "md", "sm", "xs")


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="", help="what to search for")
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"how many candidates to bring back (max {MAX_COUNT})",
    )
    return parser.parse_args(argv)


def build_url(key, query, count, customer):
    base = SEARCH_URL if query else TRENDING_URL
    parameters = urllib.parse.urlencode({"customer_id": customer, "per_page": count})
    return base.format(key=key, query=urllib.parse.quote(query)) + "&" + parameters


def request_candidates(key, query, count, customer):
    answer = get_json(build_url(key, query, count, customer))
    if not isinstance(answer, dict) or not answer.get("result"):
        raise MediaRequestRefused("the gif search came back empty handed")
    found = answer.get("data", {}).get("data", [])
    if not found:
        raise MediaRequestRefused(
            f"nothing came back for {query or 'trending'}; try other words"
        )
    return found[:count]


def choose_rendition(item, size_limit):
    """The largest tier that still fits, so quality drops only when it must."""
    renditions = item.get("file", {})
    for tier in TIER_ORDER:
        rendition = renditions.get(tier, {}).get("gif", {})
        url = rendition.get("url")
        if url and rendition.get("size", size_limit + 1) <= size_limit:
            return url
    return None


def download_candidate(media_directory, item):
    """One file to judge by, plus the good copy when the small one is not it."""
    preview_url = choose_rendition(item, PREVIEW_SIZE_LIMIT)
    sendable_url = choose_rendition(item, ATTACHMENT_SIZE_LIMIT)
    if not preview_url or not sendable_url:
        return None
    preview = write_media_file(
        media_directory, "gif-look", ".gif", fetch_bytes(preview_url)
    )
    if sendable_url == preview_url:
        return {
            "title": item.get("title", "untitled"),
            "look": preview,
            "send": preview,
        }
    sendable = write_media_file(
        media_directory, "gif", ".gif", fetch_bytes(sendable_url)
    )
    return {"title": item.get("title", "untitled"), "look": preview, "send": sendable}


def report(candidates):
    for position, candidate in enumerate(candidates, start=1):
        print(f"candidate {position}: {candidate['title']}")
        print(f"  open this to judge it: {candidate['look']}")
        print(f"  attach this one if you pick it: {candidate['send']}")


def main(argv):
    arguments = parse_arguments(argv)
    key = ""
    try:
        key = read_api_key(SECRET_NAME)
        media_directory = resolve_media_directory(".")
        query = (
            flatten_prompt(arguments.query, QUERY_LENGTH_LIMIT)
            if arguments.query.strip()
            else ""
        )
        count = max(1, min(arguments.count, MAX_COUNT))
        claim_daily_allowance(
            media_directory, "gif", DAILY_LIMIT, datetime.date.today()
        )
        found = request_candidates(key, query, count, media_directory.parent.name)
        candidates = [
            candidate
            for candidate in (
                download_candidate(media_directory, item) for item in found
            )
            if candidate
        ]
        if not candidates:
            raise MediaRequestRefused("every candidate came back too big to send")
    except MediaRequestRefused as refusal:
        # The key rides in the request path, so anything the provider echoes back
        # could carry it into the channel.
        reported = str(refusal)
        print(reported.replace(key, "***") if key else reported, file=sys.stderr)
        return 1
    report(candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
