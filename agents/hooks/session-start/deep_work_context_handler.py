from __future__ import annotations

import os
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

from hook_dispatch import HandlerResult  # noqa: E402

DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE = "DEEP_WORK_CONTEXT_DIRECTORY"
DEEP_WORK_DIRECTORY_RELATIVE_TO_HOME = ".dotfiles/.deep-work"
CONTEXT_FILENAME = "context.md"


def deep_work_directory() -> Path:
    configured_directory = os.environ.get(DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE)
    if configured_directory:
        return Path(configured_directory)
    return Path.home() / DEEP_WORK_DIRECTORY_RELATIVE_TO_HOME


def active_deep_work_context_documents() -> list[str]:
    try:
        context_files = sorted(deep_work_directory().glob(f"*/{CONTEXT_FILENAME}"))
    except OSError:
        return []
    documents = []
    for context_file in context_files:
        try:
            document = context_file.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if document:
            documents.append(document)
    return documents


def handle(hook_input: dict):
    documents = active_deep_work_context_documents()
    if not documents:
        return None
    return HandlerResult(additional_context="\n\n".join(documents))
