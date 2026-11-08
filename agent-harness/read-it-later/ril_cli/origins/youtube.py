from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from origins.transport import OriginTransport, OriginUnavailable, bounded_text

YOUTUBE_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com")
SHORT_LINK_HOST = "youtu.be"
PATH_VIDEO_ID = re.compile(r"^/(?:shorts|embed|live)/(?P<video>[\w-]{6,})")
FALLBACK_LANGUAGE = "en"
ORIGINAL_TRACK_SUFFIX = "-orig"
TIMING_LINE = re.compile(r"^\d{2}:\d{2}[:.\d]* --> ")
CUE_TAG = re.compile(r"<[^>]+>")
DESCRIPTION_CHARACTER_LIMIT = 1500


def youtube_video_id(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.hostname == SHORT_LINK_HOST:
        return parts.path.strip("/") or None
    if parts.hostname not in YOUTUBE_HOSTS:
        return None
    matched_path = PATH_VIDEO_ID.match(parts.path)
    if matched_path:
        return matched_path.group("video")
    return next(iter(parse_qs(parts.query).get("v", [])), None)


def is_caption_text(vtt_line: str) -> bool:
    stripped_line = vtt_line.strip()
    if not stripped_line or stripped_line.isdigit():
        return False
    if stripped_line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
        return False
    return not TIMING_LINE.match(stripped_line)


def transcript_from_vtt(vtt_text: str) -> str:
    caption_lines = [
        CUE_TAG.sub("", line).strip()
        for line in vtt_text.splitlines()
        if is_caption_text(line)
    ]
    deduplicated_lines = [
        line
        for position, line in enumerate(caption_lines)
        if position == 0 or line != caption_lines[position - 1]
    ]
    return " ".join(line for line in deduplicated_lines if line)


def video_language(metadata: dict) -> str:
    return str(metadata.get("language") or FALLBACK_LANGUAGE).split("-")[0]


def automatic_track(metadata: dict, language: str) -> str | None:
    automatic = list(metadata.get("automatic_captions") or {})
    preferred = f"{language}{ORIGINAL_TRACK_SUFFIX}"
    if preferred in automatic:
        return preferred
    return next(
        (code for code in automatic if code.endswith(ORIGINAL_TRACK_SUFFIX)), None
    )


def subtitle_choice(metadata: dict) -> tuple[str, str] | None:
    language = video_language(metadata)
    manual = [
        code
        for code in metadata.get("subtitles") or {}
        if code.split("-")[0] == language
    ]
    if manual:
        return "--write-subs", manual[0]
    chosen = automatic_track(metadata, language)
    return ("--write-auto-subs", chosen) if chosen else None


def subtitle_arguments(
    url: str, choice: tuple[str, str], output_template: str
) -> list[str]:
    track_flag, language = choice
    return [
        "yt-dlp",
        "--skip-download",
        "--no-warnings",
        track_flag,
        "--sub-langs",
        language,
        "--sub-format",
        "vtt",
        "-o",
        output_template,
        url,
    ]


def read_transcript(url: str, metadata: dict, transport: OriginTransport) -> str:
    choice = subtitle_choice(metadata)
    if choice is None:
        return ""
    with tempfile.TemporaryDirectory(prefix="ril-subtitles-") as subtitle_directory:
        transport.run(subtitle_arguments(url, choice, f"{subtitle_directory}/%(id)s"))
        subtitle_files = sorted(Path(subtitle_directory).glob("*.vtt"))
        if not subtitle_files:
            return ""
        return transcript_from_vtt(
            subtitle_files[0].read_text(encoding="utf-8", errors="replace")
        )


def transcript_or_reason(
    url: str, metadata: dict, transport: OriginTransport
) -> tuple[str, str]:
    try:
        return read_transcript(url, metadata, transport), ""
    except OriginUnavailable as error:
        return "", str(error)


def resolve_youtube_video(url: str, transport: OriginTransport) -> dict:
    metadata = json.loads(
        transport.run(
            ["yt-dlp", "--dump-json", "--skip-download", "--no-warnings", url]
        )
    )
    transcript, transcript_failure = transcript_or_reason(url, metadata, transport)
    return {
        "adapter": "youtube",
        "origin_id": metadata.get("id") or youtube_video_id(url),
        "title": metadata.get("title", ""),
        "channel": metadata.get("channel") or metadata.get("uploader", ""),
        "duration_seconds": metadata.get("duration"),
        "upload_date": metadata.get("upload_date", ""),
        "description": (metadata.get("description") or "")[
            :DESCRIPTION_CHARACTER_LIMIT
        ],
        "text": bounded_text(transcript),
        "transcript_failure": transcript_failure,
        "needs_browser": False,
        "browser_reason": "",
    }
