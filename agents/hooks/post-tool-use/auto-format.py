#!/usr/bin/env python3

from __future__ import annotations

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

from auto_format_handler import handle  # noqa: E402
from hook_dispatch import read_hook_input_or_exit  # noqa: E402


def main() -> None:
    hook_input = read_hook_input_or_exit()
    handle(hook_input)
    sys.exit(0)


if __name__ == "__main__":
    main()
