import json
import os
import re
import stat
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RECIPIENT = "castro.lucas290@gmail.com"
CHANNEL = "UC6Vso0wnLrqyf60Nn-rrpfw"
ENABLED_AT = "2026-10-10T00:00:00+00:00"


def read_json(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor) as stream:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("Expected a regular notification file")
        content = stream.read(65537)
    if len(content) > 65536:
        raise ValueError("Notification input too large")
    return json.loads(content)


def save(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def publication_event(directory):
    if directory.resolve() != directory:
        raise ValueError("Symlinked publication directory")
    publication = read_json(directory / "publication.json")
    status = read_json(directory / "status.json")
    if publication["status"] != "published" or status != publication:
        raise ValueError("Publication is not complete")
    if read_json(directory / "config.json")["channel_id"] != CHANNEL:
        raise ValueError("Unexpected publication channel")
    return event_for(directory, publication)


def event_for(directory, publication):
    video_id = publication["video_id"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Invalid published video ID")
    expected_url = f"https://www.youtube.com/shorts/{video_id}"
    if publication["url"] != expected_url:
        raise ValueError("Unexpected publication URL")
    published = datetime.fromisoformat(publication["published_at"])
    if published < datetime.fromisoformat(ENABLED_AT):
        raise ValueError("Publication predates notification activation")
    return {
        "video_id": video_id,
        "url": expected_url,
        "title": read_json(directory / "episode.json")["title"],
        "run_id": directory.name,
        "recovered": (directory / "recovery-attempts").is_dir(),
        "published_at": publication["published_at"],
    }


def recent_runs(root, now=None):
    today = (now or datetime.now(ZoneInfo("America/Sao_Paulo"))).date()
    for offset in range(7):
        day = today - timedelta(days=offset)
        for hour in (9, 15, 21):
            yield root / "runs" / f"{day.isoformat()}-{hour:02d}00"


def collect(root, ledger):
    for directory in recent_runs(root):
        try:
            event = publication_event(directory)
        except (OSError, ValueError, KeyError, TypeError):
            continue
        target = ledger / f"{event['video_id']}.json"
        if target.exists():
            continue
        try:
            save(target, initial_record(directory, event))
        except (OSError, ValueError, KeyError, TypeError):
            continue


def pending(ledger):
    records = ((path, read_json(path)) for path in ledger.glob("*.json"))
    waiting = [pair for pair in records if pair[1]["status"] == "pending"]
    yield from sorted(waiting, key=lambda pair: pair[1].get("attempted_at", ""))


def initial_record(directory, event):
    record = {"status": "pending", "event": event, "attempts": 0}
    try:
        receipt = read_json(directory / "email-notification.json")
    except FileNotFoundError:
        return record
    identity = (receipt["video_id"], receipt["recipient"])
    if identity != (event["video_id"], RECIPIENT):
        raise ValueError("Notification receipt identity differs")
    if receipt["status"] not in ("sent", "delivery_uncertain"):
        raise ValueError("Unexpected external notification status")
    record.update(status=receipt["status"], external_receipt=receipt)
    return record
