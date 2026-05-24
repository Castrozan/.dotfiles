#!/usr/bin/env python3
"""Fail if any tracked code file exceeds the blocking line-count threshold.

Walks `git ls-files`, filters by code extensions, counts lines, and:
  - exits 1 listing every offender above LINE_COUNT_BLOCKING_THRESHOLD
  - prints (but does not fail on) files above LINE_COUNT_WARNING_THRESHOLD

Shares thresholds and the extension list with the Write/Edit hook via
agents/hooks/post-tool-use/line_count_policy.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SHARED_POLICY_DIRECTORY = REPOSITORY_ROOT / "agents" / "hooks" / "post-tool-use"

sys.path.insert(0, str(SHARED_POLICY_DIRECTORY))

from line_count_policy import (  # noqa: E402
    LINE_COUNT_BLOCKING_THRESHOLD,
    LINE_COUNT_WARNING_THRESHOLD,
    count_lines_in_file,
    file_path_has_code_extension,
)


def list_tracked_files_in_repository() -> list[Path]:
    completed_process = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
    )
    tracked_file_paths = []
    for relative_path_text in completed_process.stdout.splitlines():
        if not relative_path_text.strip():
            continue
        absolute_path = REPOSITORY_ROOT / relative_path_text
        if absolute_path.is_file():
            tracked_file_paths.append(absolute_path)
    return tracked_file_paths


def collect_offenders_and_warnings(
    tracked_file_paths: list[Path],
) -> tuple[list[tuple[Path, int]], list[tuple[Path, int]]]:
    blocking_offenders = []
    warning_offenders = []
    for absolute_path in tracked_file_paths:
        if not file_path_has_code_extension(str(absolute_path)):
            continue
        try:
            line_count = count_lines_in_file(str(absolute_path))
        except OSError:
            continue
        if line_count > LINE_COUNT_BLOCKING_THRESHOLD:
            blocking_offenders.append((absolute_path, line_count))
        elif line_count > LINE_COUNT_WARNING_THRESHOLD:
            warning_offenders.append((absolute_path, line_count))
    blocking_offenders.sort(key=lambda entry: entry[1], reverse=True)
    warning_offenders.sort(key=lambda entry: entry[1], reverse=True)
    return blocking_offenders, warning_offenders


def format_relative_path(absolute_path: Path) -> str:
    return str(absolute_path.relative_to(REPOSITORY_ROOT))


def print_warning_section(warning_offenders: list[tuple[Path, int]]) -> None:
    if not warning_offenders:
        return
    print(
        f"WARNINGS ({len(warning_offenders)} files > "
        f"{LINE_COUNT_WARNING_THRESHOLD} lines):",
        file=sys.stderr,
    )
    for absolute_path, line_count in warning_offenders:
        print(
            f"  {line_count:>5} {format_relative_path(absolute_path)}",
            file=sys.stderr,
        )


def print_failure_section(blocking_offenders: list[tuple[Path, int]]) -> None:
    print(
        f"FAILED: {len(blocking_offenders)} files exceed "
        f"{LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit:",
        file=sys.stderr,
    )
    for absolute_path, line_count in blocking_offenders:
        print(
            f"  {line_count:>5} {format_relative_path(absolute_path)}",
            file=sys.stderr,
        )
    print(
        "\nSplit each file into smaller modules with single responsibilities.",
        file=sys.stderr,
    )


def main() -> int:
    tracked_file_paths = list_tracked_files_in_repository()
    blocking_offenders, warning_offenders = collect_offenders_and_warnings(
        tracked_file_paths
    )

    print_warning_section(warning_offenders)

    if not blocking_offenders:
        print("line-count check: OK")
        return 0

    print_failure_section(blocking_offenders)
    return 1


if __name__ == "__main__":
    sys.exit(main())
