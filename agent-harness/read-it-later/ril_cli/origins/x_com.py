from __future__ import annotations

import re
from urllib.parse import urlsplit

from origins.transport import OriginTransport, bounded_text

X_HOSTS = (
    "x.com",
    "twitter.com",
    "mobile.twitter.com",
    "mobile.x.com",
    "www.x.com",
    "www.twitter.com",
)
STATUS_PATH = re.compile(r"^/(?P<user>[^/]+)/status(?:es)?/(?P<status>\d+)")
FXTWITTER_STATUS_URL = "https://api.fxtwitter.com/{user}/status/{status}"


def x_status_reference(url: str) -> tuple[str, str] | None:
    parts = urlsplit(url)
    if parts.hostname not in X_HOSTS:
        return None
    matched_path = STATUS_PATH.match(parts.path)
    if matched_path is None:
        return None
    return matched_path.group("user"), matched_path.group("status")


def expanded_links(post: dict) -> list[str]:
    facets = (post.get("raw_text") or {}).get("facets") or []
    return [
        str(facet.get("replacement") or facet.get("original"))
        for facet in facets
        if facet.get("type") == "url"
    ]


def media_types(post: dict) -> list[str]:
    return [
        str(item.get("type")) for item in (post.get("media") or {}).get("all") or []
    ]


def article_summary(post: dict) -> dict | None:
    article = post.get("article")
    if not article:
        return None
    return {
        "title": article.get("title", ""),
        "preview": article.get("preview_text", ""),
    }


def post_summary(post: dict) -> dict:
    return {
        "author": (post.get("author") or {}).get("screen_name", ""),
        "text": bounded_text(post.get("text") or ""),
        "article": article_summary(post),
        "media_types": media_types(post),
        "links": expanded_links(post),
    }


def carries_only_images(summary: dict) -> bool:
    has_words = bool(summary["text"]) or summary["article"] is not None
    return not has_words and bool(summary["media_types"])


def resolve_x_status(url: str, transport: OriginTransport) -> dict:
    user, status = x_status_reference(url)
    post = (
        transport.json(FXTWITTER_STATUS_URL.format(user=user, status=status)).get(
            "tweet"
        )
        or {}
    )
    summary = post_summary(post)
    quoted_post = post.get("quote")
    return {
        "adapter": "x.com",
        "origin_id": status,
        **summary,
        "quoted": post_summary(quoted_post) if quoted_post else None,
        "needs_browser": carries_only_images(summary),
        "browser_reason": "image-only post" if carries_only_images(summary) else "",
    }
