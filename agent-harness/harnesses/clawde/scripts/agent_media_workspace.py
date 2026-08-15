"""Workspace, secret and budget rules shared by the agent media tools.

Both tools write a file into the calling agent's own workspace and print its
absolute path, which is what the channel plugin's reply tool takes as an
attachment. Everything a guest can influence - the prompt, the reference image,
how often either runs - is bounded here rather than in the agent's judgement.
"""

import json
import os
import time
import uuid
from pathlib import Path

MEDIA_DIRECTORY_NAME = "media"
USAGE_FILE_NAME = "usage.json"
RETENTION_DAYS = 7


class MediaRequestRefused(Exception):
    pass


def agents_directory():
    configured = os.environ.get("CLAWDE_AGENTS_DIRECTORY")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / "clawde").resolve()


def secrets_directory():
    configured = os.environ.get("CLAWDE_SECRETS_DIRECTORY")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".secrets").resolve()


def resolve_media_directory(working_directory):
    workspace = Path(working_directory).resolve()
    if workspace.parent != agents_directory():
        raise MediaRequestRefused(
            f"refusing to write media from {workspace}: "
            f"only an agent workspace directly under {agents_directory()} owns a media directory"
        )
    return workspace / MEDIA_DIRECTORY_NAME


def channel_inbox_directories(media_directory):
    """Directories a reference image may be read from: what the channel downloaded, and our own output."""
    configured = os.environ.get("DISCORD_STATE_DIR")
    if configured:
        return [media_directory, Path(configured).expanduser() / "inbox"]
    agent_name = media_directory.parent.name
    home_inbox = Path.home() / ".claude" / "channels" / "discord" / agent_name / "inbox"
    return [media_directory, home_inbox]


def resolve_reference_file(reference, media_directory):
    """A reference must be something the channel handed us, never an arbitrary path off this machine."""
    try:
        candidate = Path(reference).expanduser().resolve(strict=True)
    except OSError:
        raise MediaRequestRefused(f"no such reference image: {reference}") from None
    for allowed in channel_inbox_directories(media_directory):
        try:
            candidate.relative_to(allowed.resolve())
        except (OSError, ValueError):
            continue
        return candidate
    raise MediaRequestRefused(
        f"refusing to upload {candidate}: a reference image must come from an attachment "
        "the channel downloaded, or from a file this tool generated earlier"
    )


def read_api_key(secret_name):
    key_file = secrets_directory() / secret_name
    try:
        key = key_file.read_text(encoding="utf-8").strip()
    except OSError:
        raise MediaRequestRefused(
            f"this machine holds no {secret_name}, so that is not something you can do here"
        ) from None
    if not key:
        raise MediaRequestRefused(f"the key at {key_file} is empty")
    return key


def flatten_prompt(prompt, limit):
    flattened = " ".join(prompt.split())
    if not flattened:
        raise MediaRequestRefused("refusing an empty prompt")
    if len(flattened) > limit:
        raise MediaRequestRefused(
            f"refusing a {len(flattened)} character prompt: keep it under {limit}"
        )
    return flattened


def claim_daily_allowance(media_directory, kind, limit, today):
    """Count one use against today's budget, refusing once the day is spent."""
    media_directory.mkdir(parents=True, exist_ok=True)
    usage_file = media_directory / USAGE_FILE_NAME
    try:
        recorded = json.loads(usage_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        recorded = {}
    spent = recorded.get(today.isoformat(), {}) if isinstance(recorded, dict) else {}
    already = spent.get(kind, 0) if isinstance(spent, dict) else 0
    if already >= limit:
        raise MediaRequestRefused(
            f"today's {kind} budget is spent ({already}/{limit}); it resets tomorrow"
        )
    usage_file.write_text(
        json.dumps({today.isoformat(): {**spent, kind: already + 1}}), encoding="utf-8"
    )
    return already + 1


def prune_expired_media(media_directory, now):
    """Generated media is disposable once Discord holds its own copy."""
    cutoff = now - RETENTION_DAYS * 86400
    for path in media_directory.glob("*"):
        if path.name == USAGE_FILE_NAME or not path.is_file():
            continue
        if path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)


def write_media_file(media_directory, prefix, suffix, payload):
    media_directory.mkdir(parents=True, exist_ok=True)
    media_file = media_directory / f"{prefix}-{uuid.uuid4().hex[:12]}{suffix}"
    media_file.write_bytes(payload)
    prune_expired_media(media_directory, time.time())
    return media_file
