#!/usr/bin/env python3

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

PROCESSED_MARKER = "#agent-work-done"
CAPTURE_TIMESTAMP_IN_FILENAME = re.compile(
    r"(\d{4}-\d{2}-\d{2})[ _](\d{2})-(\d{2})-(\d{2})"
)


def default_capture_inbox_directory() -> Path:
    vault_directory = Path(os.environ.get("OBSIDIAN_HOME") or Path.home() / "vault")
    return vault_directory / "ReadItLater Inbox"


def capture_timestamp_from_filename(capture_filename: str) -> datetime | None:
    matched_timestamp = CAPTURE_TIMESTAMP_IN_FILENAME.search(capture_filename)
    if matched_timestamp is None:
        return None
    day, hour, minute, second = matched_timestamp.groups()
    try:
        return datetime.strptime(f"{day} {hour}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def capture_ordering_timestamp(capture_path: Path) -> datetime:
    timestamp_from_filename = capture_timestamp_from_filename(capture_path.name)
    if timestamp_from_filename is not None:
        return timestamp_from_filename
    return datetime.fromtimestamp(capture_path.stat().st_mtime).replace(microsecond=0)


def capture_is_unprocessed(capture_path: Path) -> bool:
    return PROCESSED_MARKER not in capture_path.read_text(
        encoding="utf-8", errors="replace"
    )


def collect_unprocessed_captures(
    capture_inbox_directory: Path,
) -> list[dict[str, str]]:
    if not capture_inbox_directory.is_dir():
        return []
    unprocessed_capture_paths = sorted(
        (
            capture_path
            for capture_path in capture_inbox_directory.glob("*.md")
            if capture_is_unprocessed(capture_path)
        ),
        key=lambda capture_path: (
            capture_ordering_timestamp(capture_path),
            capture_path.name,
        ),
        reverse=True,
    )
    return [
        {
            "name": capture_path.name,
            "path": str(capture_path),
            "captured": capture_ordering_timestamp(capture_path).isoformat(sep=" "),
            "captured_from": (
                "filename"
                if capture_timestamp_from_filename(capture_path.name)
                else "modification-time"
            ),
        }
        for capture_path in unprocessed_capture_paths
    ]


def render_unprocessed_captures_as_text(
    unprocessed_captures: list[dict[str, str]], total_count: int
) -> str:
    rendered_rows = [
        f"{position:>4}  {capture['captured']}  {capture['name']}"
        for position, capture in enumerate(unprocessed_captures, 1)
    ]
    header = f"{total_count} unprocessed captures, newest first"
    if len(unprocessed_captures) < total_count:
        header = f"{header}, showing {len(unprocessed_captures)}"
    return "\n".join([header, *rendered_rows])


def build_argument_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="List unworked ReadItLater captures, newest first."
    )
    argument_parser.add_argument(
        "--inbox", type=Path, default=default_capture_inbox_directory()
    )
    argument_parser.add_argument("--limit", type=int, default=20)
    argument_parser.add_argument("--json", action="store_true")
    return argument_parser


def main() -> int:
    parsed_arguments = build_argument_parser().parse_args()
    unprocessed_captures = collect_unprocessed_captures(parsed_arguments.inbox)
    total_count = len(unprocessed_captures)
    if parsed_arguments.limit > 0:
        unprocessed_captures = unprocessed_captures[: parsed_arguments.limit]
    if parsed_arguments.json:
        print(
            json.dumps(
                {"total": total_count, "captures": unprocessed_captures}, indent=2
            )
        )
        return 0
    print(render_unprocessed_captures_as_text(unprocessed_captures, total_count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
