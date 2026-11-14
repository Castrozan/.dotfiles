import os
import re
import shutil
from pathlib import Path

from shorts_recovery import pending_recoveries
from shorts_store import RUN_STATUS_FILENAME, read_document, write_document

RETAINED_RUNS = 5
INTERMEDIATE_MINIMUM_BYTES = 1024 * 1024
AUDIT_TRAIL_FILES = ("agent-events.jsonl",)
RETENTION_FILENAME = "retention.json"
RUN_IDENTIFIER = re.compile(r"\d{4}-\d{2}-\d{2}-\d{4}")


def episode_files(directory):
    episode = read_document(directory / "episode.json")
    return [
        episode["video"],
        episode["narration"]["file"],
        *(beat["frame"] for beat in episode["beats"]),
        *(review["evidence"] for review in episode["review"].values()),
    ]


def retained_files(directory):
    names = [*episode_files(directory), *AUDIT_TRAIL_FILES]
    return {(directory / name).resolve() for name in names}


def intermediate_files(directory):
    retained = retained_files(directory)
    for parent, _, names in os.walk(directory):
        for name in names:
            path = Path(parent) / name
            if path.is_symlink() or path.resolve() in retained:
                continue
            if path.stat().st_size >= INTERMEDIATE_MINIMUM_BYTES:
                yield path


def remove_empty_directories(directory):
    for parent, _, _ in os.walk(directory, topdown=False):
        path = Path(parent)
        if path != directory and not path.is_symlink() and not any(path.iterdir()):
            path.rmdir()


def discard_intermediates(directory):
    if read_document(directory / RUN_STATUS_FILENAME)["status"] != "published":
        return None
    discarded = []
    for path in list(intermediate_files(directory)):
        discarded.append(
            {"path": str(path.relative_to(directory)), "bytes": path.stat().st_size}
        )
        path.unlink()
    remove_empty_directories(directory)
    record = {
        "discarded_files": discarded,
        "discarded_bytes": sum(entry["bytes"] for entry in discarded),
    }
    write_document(directory / RETENTION_FILENAME, record)
    return record


def scheduled_runs(root):
    runs = root / "runs"
    if not runs.is_dir():
        return []
    return sorted(
        (
            path
            for path in runs.iterdir()
            if path.is_dir()
            and not path.is_symlink()
            and RUN_IDENTIFIER.fullmatch(path.name)
        ),
        key=lambda path: path.name,
        reverse=True,
    )


def prune_runs(root):
    protected = pending_recoveries(root)
    pruned = [
        path
        for path in scheduled_runs(root)[RETAINED_RUNS:]
        if path.name not in protected
    ]
    for path in pruned:
        shutil.rmtree(path)
    return [path.name for path in pruned]
