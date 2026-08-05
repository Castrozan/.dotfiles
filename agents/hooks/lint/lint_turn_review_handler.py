#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
from collections import OrderedDict

hook_script_directory = os.path.dirname(os.path.realpath(__file__))
shared_common_hook_modules_directory = os.path.join(
    os.path.dirname(hook_script_directory), "common"
)
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
):
    if os.path.isdir(importable_directory) and importable_directory not in sys.path:
        sys.path.insert(0, importable_directory)

from hook_dispatch import HandlerResult  # noqa: E402
from lint_ledger import read_and_clear_edited_source_files  # noqa: E402
from linter_table_by_extension import LINTERS_BY_FILE_EXTENSION  # noqa: E402
from repo_native_lint_command_detection import (  # noqa: E402
    detect_repository_native_lint_command,
    find_repository_root_for_file,
)


def group_existing_files_by_repository(
    edited_files: list[str],
) -> "OrderedDict[str, list[str]]":
    files_by_repository: OrderedDict[str, list[str]] = OrderedDict()
    for edited_file in edited_files:
        if not os.path.exists(edited_file):
            continue
        repository_root = find_repository_root_for_file(edited_file)
        files_by_repository.setdefault(repository_root, []).append(edited_file)
    return files_by_repository


def linter_names_for_edited_files(files: list[str]) -> list[str]:
    linter_names: list[str] = []
    for edited_file in files:
        _, file_extension = os.path.splitext(edited_file)
        for linter in LINTERS_BY_FILE_EXTENSION.get(file_extension.lower(), []):
            if linter["name"] not in linter_names:
                linter_names.append(linter["name"])
    return linter_names


def build_repository_advisory(repository_root: str, files: list[str]) -> str | None:
    repository_label = os.path.basename(repository_root) or repository_root
    native_lint_command = detect_repository_native_lint_command(repository_root)
    if native_lint_command:
        return (
            f"{repository_label}: {len(files)} file(s) changed this turn; "
            f"lint before pushing with `{native_lint_command}`"
        )
    linter_names = linter_names_for_edited_files(files)
    if not linter_names:
        return None
    return (
        f"{repository_label}: {len(files)} file(s) changed this turn; "
        f"no repo lint command detected, run {', '.join(linter_names)} before pushing"
    )


def handle(hook_input: dict):
    edited_files = read_and_clear_edited_source_files(hook_input.get("session_id", ""))
    if not edited_files:
        return None

    advisories: list[str] = []
    for repository_root, files in group_existing_files_by_repository(
        edited_files
    ).items():
        advisory = build_repository_advisory(repository_root, files)
        if advisory:
            advisories.append(advisory)

    if not advisories:
        return None
    return HandlerResult(system_message="\n".join(advisories))
