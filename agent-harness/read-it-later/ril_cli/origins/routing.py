from __future__ import annotations

import json

from origins.transport import OriginTransport, OriginUnavailable
from origins.web_page import resolve_web_page
from origins.x_com import resolve_x_status, x_status_reference
from origins.youtube import resolve_youtube_video, youtube_video_id


def origin_adapter(url: str):
    if x_status_reference(url):
        return "x.com", resolve_x_status
    if youtube_video_id(url):
        return "youtube", resolve_youtube_video
    return "web", resolve_web_page


def origin_identifier(url: str | None) -> str:
    if not url:
        return ""
    x_reference = x_status_reference(url)
    if x_reference:
        return x_reference[1]
    return youtube_video_id(url) or url


def resolve_origin(url: str | None, transport: OriginTransport) -> dict:
    if not url:
        return {
            "adapter": "none",
            "origin_id": "",
            "needs_browser": False,
            "error": "capture carries no link",
        }
    adapter_name, resolve = origin_adapter(url)
    try:
        return resolve(url, transport)
    except (OriginUnavailable, json.JSONDecodeError, ValueError) as error:
        return {
            "adapter": adapter_name,
            "origin_id": origin_identifier(url),
            "needs_browser": True,
            "browser_reason": f"automatic read failed: {error}",
        }
