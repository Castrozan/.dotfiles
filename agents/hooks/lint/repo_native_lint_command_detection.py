from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def find_repository_root_for_file(file_path: str) -> str:
    start_directory = os.path.dirname(os.path.abspath(file_path)) or "."
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start_directory,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return start_directory


def _package_json_declares_lint_script(repository_root: str) -> bool:
    try:
        package_manifest = json.loads(
            (Path(repository_root) / "package.json").read_text()
        )
    except (OSError, json.JSONDecodeError):
        return False
    scripts = package_manifest.get("scripts")
    return isinstance(scripts, dict) and "lint" in scripts


def _makefile_declares_lint_target(repository_root: str) -> bool:
    try:
        lines = (Path(repository_root) / "Makefile").read_text().splitlines()
    except OSError:
        return False
    return any(line.startswith("lint:") for line in lines)


def _justfile_declares_lint_recipe(repository_root: str) -> bool:
    for justfile_name in ("justfile", "Justfile", ".justfile"):
        try:
            lines = (Path(repository_root) / justfile_name).read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            stripped = line.strip()
            if (
                stripped == "lint:"
                or stripped.startswith("lint:")
                or stripped.startswith("lint ")
            ):
                return True
    return False


def detect_repository_native_lint_command(repository_root: str) -> str | None:
    if (Path(repository_root) / ".pre-commit-config.yaml").exists():
        return "pre-commit run --all-files"
    if _package_json_declares_lint_script(repository_root):
        return "npm run lint"
    if _makefile_declares_lint_target(repository_root):
        return "make lint"
    if _justfile_declares_lint_recipe(repository_root):
        return "just lint"
    return None
