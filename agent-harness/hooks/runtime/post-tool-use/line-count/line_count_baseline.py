"""Grandfathered line-count ceilings recorded by the repository owning a file."""

from __future__ import annotations

import json
import os

from line_count_policy import LINE_COUNT_BLOCKING_THRESHOLD

BASELINE_RELATIVE_PATH = os.path.join(
    "repository", "verification", "line-count-baseline.json"
)


def grandfathered_line_counts(baseline_file_path: str) -> dict[str, int]:
    try:
        with open(baseline_file_path, encoding="utf-8") as baseline_file:
            recorded_line_counts = json.load(baseline_file)
    except (OSError, ValueError):
        return {}
    if not isinstance(recorded_line_counts, dict):
        return {}
    return {
        relative_path: line_count
        for relative_path, line_count in recorded_line_counts.items()
        if isinstance(line_count, int)
        and not isinstance(line_count, bool)
        and line_count > LINE_COUNT_BLOCKING_THRESHOLD
    }


def repository_root_recording_line_counts(file_path: str) -> str | None:
    candidate_root = os.path.dirname(os.path.abspath(file_path))
    while True:
        if os.path.isfile(os.path.join(candidate_root, BASELINE_RELATIVE_PATH)):
            return candidate_root
        parent_directory = os.path.dirname(candidate_root)
        if parent_directory == candidate_root:
            return None
        candidate_root = parent_directory


def allowed_line_count_for_file(file_path: str) -> int:
    repository_root = repository_root_recording_line_counts(file_path)
    if repository_root is None:
        return LINE_COUNT_BLOCKING_THRESHOLD
    relative_path = os.path.relpath(os.path.abspath(file_path), repository_root)
    return grandfathered_line_counts(
        os.path.join(repository_root, BASELINE_RELATIVE_PATH)
    ).get(relative_path, LINE_COUNT_BLOCKING_THRESHOLD)
