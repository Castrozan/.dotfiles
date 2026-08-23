#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SHARED_POLICY_DIRECTORY = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "hooks"
    / "runtime"
    / "post-tool-use"
    / "line-count"
)
BASELINE_FILE_PATH = Path(__file__).resolve().parent / "line-count-baseline.json"

sys.path.insert(0, str(SHARED_POLICY_DIRECTORY))

from line_count_baseline import grandfathered_line_counts  # noqa: E402
from line_count_policy import (  # noqa: E402
    LINE_COUNT_BLOCKING_THRESHOLD,
    line_count_violation,
)


@dataclass(frozen=True)
class BaselineDrift:
    file_path: str
    current_line_count: int | None
    recorded_line_count: int | None


def list_tracked_file_paths() -> list[Path]:
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


def line_count_per_over_limit_file() -> dict[str, int]:
    over_limit_files = {}
    for absolute_path in list_tracked_file_paths():
        violation = line_count_violation(
            str(absolute_path), LINE_COUNT_BLOCKING_THRESHOLD
        )
        if violation is None:
            continue
        relative_path = str(absolute_path.relative_to(REPOSITORY_ROOT))
        over_limit_files[relative_path] = violation.line_count
    return over_limit_files


def write_grandfathered_line_counts(over_limit_files: dict[str, int]) -> None:
    serialized = json.dumps(dict(sorted(over_limit_files.items())), indent=2)
    BASELINE_FILE_PATH.write_text(serialized + "\n")


def drift_from_baseline(
    current_over_limit_files: dict[str, int],
    grandfathered_ceilings: dict[str, int],
) -> list[BaselineDrift]:
    return [
        BaselineDrift(
            relative_path,
            current_over_limit_files.get(relative_path),
            grandfathered_ceilings.get(relative_path),
        )
        for relative_path in sorted(
            set(current_over_limit_files) | set(grandfathered_ceilings)
        )
        if current_over_limit_files.get(relative_path)
        != grandfathered_ceilings.get(relative_path)
    ]


def describe_drift(drift: BaselineDrift) -> str:
    if drift.recorded_line_count is None:
        return (
            f"new offender at {drift.current_line_count} lines, over the "
            f"{LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit"
        )
    if drift.current_line_count is None:
        return (
            f"grandfathered at {drift.recorded_line_count}, no longer a tracked "
            f"file over the limit; drop the entry"
        )
    if drift.current_line_count > drift.recorded_line_count:
        return (
            f"grew from {drift.recorded_line_count} to {drift.current_line_count} lines"
        )
    return (
        f"shrank from {drift.recorded_line_count} to {drift.current_line_count} "
        f"lines; record the smaller ceiling"
    )


def print_drift_failure(drifts: list[BaselineDrift]) -> None:
    print(
        f"FAILED: {len(drifts)} file(s) no longer match the line-count baseline:",
        file=sys.stderr,
    )
    for drift in drifts:
        print(f"  {drift.file_path}  ({describe_drift(drift)})", file=sys.stderr)
    print(
        "\nSplit the file into smaller single-responsibility modules, or run "
        "repository/verification/check-line-counts.py --update-baseline if the new "
        "state is intended.",
        file=sys.stderr,
    )


def main() -> int:
    current_over_limit_files = line_count_per_over_limit_file()

    if "--update-baseline" in sys.argv[1:]:
        write_grandfathered_line_counts(current_over_limit_files)
        print(
            "line-count baseline updated: "
            f"{len(current_over_limit_files)} grandfathered files"
        )
        return 0

    drifts = drift_from_baseline(
        current_over_limit_files,
        grandfathered_line_counts(str(BASELINE_FILE_PATH)),
    )
    if not drifts:
        print(
            f"line-count check: OK ({len(current_over_limit_files)} "
            "grandfathered files)"
        )
        return 0

    print_drift_failure(drifts)
    return 1


if __name__ == "__main__":
    sys.exit(main())
