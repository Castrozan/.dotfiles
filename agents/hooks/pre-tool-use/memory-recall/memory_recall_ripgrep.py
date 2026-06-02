from __future__ import annotations

import re
import subprocess
from pathlib import Path

MAX_RECALL_PATHS = 5


def ripgrep_score_per_file(
    memory_directory: Path, keywords: list[str]
) -> dict[Path, int]:
    if not keywords or not memory_directory.is_dir():
        return {}
    pattern = "|".join(re.escape(keyword) for keyword in keywords)
    try:
        completed = subprocess.run(
            [
                "rg",
                "--no-messages",
                "--ignore-case",
                "--count-matches",
                "--glob=*.md",
                "--glob=!MEMORY.md",
                pattern,
                str(memory_directory),
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}
    archive_directory_segment = f"{memory_directory.name}/archive/"
    scores: dict[Path, int] = {}
    for line in completed.stdout.splitlines():
        if ":" not in line:
            continue
        path_part, count_part = line.rsplit(":", 1)
        if archive_directory_segment in path_part:
            continue
        try:
            scores[Path(path_part)] = int(count_part)
        except ValueError:
            continue
    return scores


def select_top_recall_paths(scores: dict[Path, int]) -> list[Path]:
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [path for path, _ in ranked[:MAX_RECALL_PATHS]]
