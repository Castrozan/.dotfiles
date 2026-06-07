#!/usr/bin/env python3
"""Block files from newly exceeding the line-count hard limit.

Existing over-limit files are grandfathered in tests/line-count-baseline.json,
which maps each one to its allowed line count. The check fails when a file that
is not grandfathered exceeds the blocking threshold, or when a grandfathered
file grows beyond its recorded count. Shrinking always passes. Run with
--update-baseline to refreeze the current state after deliberately splitting or
accepting files.

Thresholds and the code-extension list are shared with the Write/Edit hook via
agents/hooks/post-tool-use/line-count/line_count_policy.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SHARED_POLICY_DIRECTORY = (
    REPOSITORY_ROOT / "agents" / "hooks" / "post-tool-use" / "line-count"
)
BASELINE_FILE_PATH = Path(__file__).resolve().parent / "line-count-baseline.json"

sys.path.insert(0, str(SHARED_POLICY_DIRECTORY))

from line_count_policy import (  # noqa: E402
    LINE_COUNT_BLOCKING_THRESHOLD,
    SEVERITY_BLOCKING,
    evaluate_code_file_line_count,
)


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
        evaluation = evaluate_code_file_line_count(str(absolute_path))
        if evaluation is None:
            continue
        line_count, severity = evaluation
        if severity == SEVERITY_BLOCKING:
            relative_path = str(absolute_path.relative_to(REPOSITORY_ROOT))
            over_limit_files[relative_path] = line_count
    return over_limit_files


def load_grandfathered_line_counts() -> dict[str, int]:
    if not BASELINE_FILE_PATH.is_file():
        return {}
    return json.loads(BASELINE_FILE_PATH.read_text())


def write_grandfathered_line_counts(over_limit_files: dict[str, int]) -> None:
    serialized = json.dumps(dict(sorted(over_limit_files.items())), indent=2)
    BASELINE_FILE_PATH.write_text(serialized + "\n")


def find_new_or_worsened_offenders(
    current_over_limit_files: dict[str, int],
    grandfathered_line_counts: dict[str, int],
) -> list[tuple[str, int, int]]:
    regressions = []
    for relative_path, line_count in sorted(current_over_limit_files.items()):
        allowed_line_count = grandfathered_line_counts.get(
            relative_path, LINE_COUNT_BLOCKING_THRESHOLD
        )
        if line_count > allowed_line_count:
            regressions.append((relative_path, line_count, allowed_line_count))
    return regressions


def print_regression_failure(regressions: list[tuple[str, int, int]]) -> None:
    print(
        f"FAILED: {len(regressions)} file(s) newly exceed the "
        f"{LINE_COUNT_BLOCKING_THRESHOLD}-line hard limit:",
        file=sys.stderr,
    )
    for relative_path, line_count, allowed_line_count in regressions:
        if allowed_line_count == LINE_COUNT_BLOCKING_THRESHOLD:
            ceiling_description = "new offender"
        else:
            ceiling_description = f"grandfathered at {allowed_line_count}"
        print(
            f"  {line_count:>5} {relative_path}  ({ceiling_description})",
            file=sys.stderr,
        )
    print(
        "\nSplit the file into smaller single-responsibility modules, or run "
        "tests/check-line-counts.py --update-baseline if the growth is intended.",
        file=sys.stderr,
    )


def main() -> int:
    if "--update-baseline" in sys.argv[1:]:
        over_limit_files = line_count_per_over_limit_file()
        write_grandfathered_line_counts(over_limit_files)
        print(
            f"line-count baseline updated: {len(over_limit_files)} grandfathered files"
        )
        return 0

    current_over_limit_files = line_count_per_over_limit_file()
    grandfathered_line_counts = load_grandfathered_line_counts()
    regressions = find_new_or_worsened_offenders(
        current_over_limit_files, grandfathered_line_counts
    )

    if not regressions:
        print(
            f"line-count check: OK ({len(grandfathered_line_counts)} "
            "grandfathered files)"
        )
        return 0

    print_regression_failure(regressions)
    return 1


if __name__ == "__main__":
    sys.exit(main())
