from __future__ import annotations

from pathlib import Path


def encode_cwd_as_claude_project_directory(absolute_cwd: Path) -> str:
    raw_path = str(absolute_cwd)
    return raw_path.replace("/", "-").replace(".", "-")


def resolve_memory_directory_for_cwd(cwd: str) -> Path:
    absolute_cwd = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    project_directory_name = encode_cwd_as_claude_project_directory(absolute_cwd)
    return Path.home() / ".claude" / "projects" / project_directory_name / "memory"
