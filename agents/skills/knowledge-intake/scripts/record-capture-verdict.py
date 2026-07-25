#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from pathlib import Path

PROCESSED_MARKER = "#agent-work-done"
VERDICT_CHOICES = ("adopt", "trial", "learn", "reference", "drop")


def default_capture_inbox_directory() -> Path:
    vault_directory = Path(os.environ.get("OBSIDIAN_HOME") or Path.home() / "vault")
    return vault_directory / "ReadItLater Inbox"


def resolve_capture_path(capture_inbox_directory: Path, capture_reference: str) -> Path:
    direct_path = Path(capture_reference).expanduser()
    if direct_path.is_file():
        return direct_path
    named_path = capture_inbox_directory / capture_reference
    if named_path.is_file():
        return named_path
    named_path_with_extension = capture_inbox_directory / f"{capture_reference}.md"
    if named_path_with_extension.is_file():
        return named_path_with_extension
    raise FileNotFoundError(f"no capture matches {capture_reference!r}")


def normalize_entry_link(second_brain_entry: str) -> str:
    return second_brain_entry.strip().strip("[]")


def build_verdict_block(
    verdict: str, outcome: str, second_brain_entry: str | None
) -> str:
    verdict_lines = [PROCESSED_MARKER, f"verdict:: {verdict}", f"outcome:: {outcome}"]
    if second_brain_entry:
        verdict_lines.append(f"entry:: [[{normalize_entry_link(second_brain_entry)}]]")
    return "\n".join(verdict_lines) + "\n"


def record_capture_verdict(
    capture_path: Path, verdict: str, outcome: str, second_brain_entry: str | None
) -> str:
    capture_body = capture_path.read_text(encoding="utf-8")
    if PROCESSED_MARKER in capture_body:
        return "already-recorded"
    verdict_block = build_verdict_block(verdict, outcome, second_brain_entry)
    capture_path.write_text(
        f"{capture_body.rstrip()}\n\n{verdict_block}", encoding="utf-8"
    )
    return "recorded"


def build_argument_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="Stamp a worked ReadItLater capture with its verdict."
    )
    argument_parser.add_argument("capture")
    argument_parser.add_argument("--verdict", required=True, choices=VERDICT_CHOICES)
    argument_parser.add_argument("--outcome", required=True)
    argument_parser.add_argument("--entry")
    argument_parser.add_argument(
        "--inbox", type=Path, default=default_capture_inbox_directory()
    )
    return argument_parser


def main() -> int:
    parsed_arguments = build_argument_parser().parse_args()
    capture_path = resolve_capture_path(
        parsed_arguments.inbox, parsed_arguments.capture
    )
    recording_outcome = record_capture_verdict(
        capture_path,
        parsed_arguments.verdict,
        parsed_arguments.outcome,
        parsed_arguments.entry,
    )
    print(f"{recording_outcome}: {capture_path.name}")
    return 0 if recording_outcome == "recorded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
