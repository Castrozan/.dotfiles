import json
import os
import time
import uuid
from pathlib import Path

from clawde_workspace_paths import agents_directory

MEDIA_DIRECTORY_NAME = "media"
USAGE_FILE_NAME = "usage.json"
RETENTION_DAYS = 7


class MediaRequestRefused(Exception):
    pass


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
