#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    _MODULE_DIRECTORY.parent / "common",
):
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from changed_file_paths import collect_changed_file_paths  # noqa: E402
from formatter_table_by_extension import FORMATTERS_BY_FILE_EXTENSION  # noqa: E402


def check_formatter_available(formatter_cmd: list[str]) -> bool:
    try:
        subprocess.run([formatter_cmd[0], "--version"], capture_output=True, timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run([formatter_cmd[0], "--help"], capture_output=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def run_formatter(file_path: str, formatter: dict) -> bool:
    cmd = formatter["cmd"] + [file_path]

    try:
        if formatter.get("redirect"):
            with open(file_path, "r") as f:
                content = f.read()

            result = subprocess.run(
                formatter["cmd"],
                input=content,
                text=True,
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                with open(file_path, "w") as f:
                    f.write(result.stdout)
                return True
            return False
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0

    except (subprocess.TimeoutExpired, Exception):
        return False


def find_file_in_ancestor_directories(start_directory: str, filename: str):
    current_directory = os.path.abspath(start_directory)
    while True:
        candidate_path = os.path.join(current_directory, filename)
        if os.path.exists(candidate_path):
            return candidate_path
        parent_directory = os.path.dirname(current_directory)
        if parent_directory == current_directory:
            return None
        current_directory = parent_directory


def repository_declares_conflicting_formatter(
    file_path: str, file_extension: str
) -> bool:
    start_directory = os.path.dirname(os.path.abspath(file_path)) or "."
    if file_extension == ".py":
        pyproject_path = find_file_in_ancestor_directories(
            start_directory, "pyproject.toml"
        )
        if pyproject_path:
            try:
                with open(pyproject_path) as pyproject_file:
                    pyproject_text = pyproject_file.read()
            except OSError:
                pyproject_text = ""
            if "[tool.black]" in pyproject_text and "[tool.ruff" not in pyproject_text:
                return True
    if file_extension in (".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml"):
        for biome_config_name in ("biome.json", "biome.jsonc"):
            if find_file_in_ancestor_directories(start_directory, biome_config_name):
                return True
    return False


def format_single_file(file_path: str) -> None:
    if not file_path or not os.path.exists(file_path):
        return

    try:
        if os.path.getsize(file_path) > 1024 * 1024:
            return
    except OSError:
        return

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in FORMATTERS_BY_FILE_EXTENSION:
        return

    if repository_declares_conflicting_formatter(file_path, ext):
        return

    for formatter in FORMATTERS_BY_FILE_EXTENSION[ext]["formatters"]:
        if check_formatter_available(formatter["cmd"]):
            run_formatter(file_path, formatter)
            return


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    for file_path in collect_changed_file_paths(data):
        format_single_file(file_path)

    sys.exit(0)


if __name__ == "__main__":
    main()
