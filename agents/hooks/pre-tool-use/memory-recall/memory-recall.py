#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import memory_recall_handler  # noqa: E402
from memory_recall_io import (  # noqa: E402
    emit_additional_context_and_exit,
    exit_silently,
    read_hook_input_from_stdin,
)
from memory_recall_memory_directory import (  # noqa: E402, F401
    resolve_memory_directory_for_cwd,
)


def main() -> None:
    hook_input = read_hook_input_from_stdin()
    result = memory_recall_handler.handle(hook_input)
    if result is None or result.additional_context is None:
        exit_silently()
    emit_additional_context_and_exit(result.additional_context)


if __name__ == "__main__":
    main()
