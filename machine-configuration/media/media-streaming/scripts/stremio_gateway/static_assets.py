import mimetypes
import urllib.parse


def static_candidate(static_root, request_path):
    relative_path = urllib.parse.unquote(request_path).lstrip("/") or "index.html"
    candidate = (static_root / relative_path).resolve()
    if not candidate.is_relative_to(static_root) or not candidate.is_file():
        return None
    return candidate


def content_type(candidate):
    return mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"


def cache_control(candidate):
    return (
        "no-cache"
        if candidate.name == "index.html"
        else "public, max-age=31536000, immutable"
    )
