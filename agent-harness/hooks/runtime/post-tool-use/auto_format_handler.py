from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    os.path.join(os.path.dirname(_MODULE_DIRECTORY), "common"),
):
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

from changed_file_paths import collect_changed_file_paths  # noqa: E402
from formatter_table_by_extension import FORMATTERS_BY_FILE_EXTENSION  # noqa: E402


def run_formatter(file_path: str, formatter: dict) -> None:
    import subprocess

    if not formatter.get("redirect"):
        subprocess.run(
            formatter["cmd"] + [file_path], capture_output=True, text=True, timeout=10
        )
        return

    with open(file_path) as source_file:
        original_content = source_file.read()

    result = subprocess.run(
        formatter["cmd"],
        input=original_content,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if result.returncode == 0:
        with open(file_path, "w") as source_file:
            source_file.write(result.stdout)


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
    if file_extension == ".py" and _python_formatter_conflicts(start_directory):
        return True
    if file_extension in (".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml"):
        return _repository_has_biome_configuration(start_directory)
    return False


def _python_formatter_conflicts(start_directory: str) -> bool:
    pyproject_path = find_file_in_ancestor_directories(
        start_directory, "pyproject.toml"
    )
    if not pyproject_path:
        return False
    try:
        with open(pyproject_path) as pyproject_file:
            pyproject_text = pyproject_file.read()
    except OSError:
        pyproject_text = ""
    return "[tool.black]" in pyproject_text and "[tool.ruff" not in pyproject_text


def _repository_has_biome_configuration(start_directory: str) -> bool:
    for biome_config_name in ("biome.json", "biome.jsonc"):
        if find_file_in_ancestor_directories(start_directory, biome_config_name):
            return True
    return False


def _file_is_small_enough_to_format(file_path: str) -> bool:
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        if os.path.getsize(file_path) > 1024 * 1024:
            return False
    except OSError:
        return False
    return True


def _formatters_for_file(file_path: str):
    if not _file_is_small_enough_to_format(file_path):
        return None
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext not in FORMATTERS_BY_FILE_EXTENSION:
        return None
    if repository_declares_conflicting_formatter(file_path, ext):
        return None
    return FORMATTERS_BY_FILE_EXTENSION[ext]["formatters"]


def format_single_file(file_path: str) -> None:
    formatters = _formatters_for_file(file_path)
    if formatters is None:
        return

    for formatter in formatters:
        try:
            run_formatter(file_path, formatter)
            return
        except FileNotFoundError:
            continue
        except Exception:
            return


def handle(hook_input: dict):
    for file_path in collect_changed_file_paths(hook_input):
        format_single_file(file_path)
    return None
