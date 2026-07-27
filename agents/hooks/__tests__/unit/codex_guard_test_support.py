import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
CODEX_TOOL_PAYLOAD_SOURCE = HOOKS_ROOT / "common" / "codex_tool_payload.py"
CHANGED_FILE_PATHS_SOURCE = HOOKS_ROOT / "common" / "changed_file_paths.py"
PRE_TOOL_USE_BLOCK_SOURCE = HOOKS_ROOT / "common" / "pre_tool_use_block.py"
HOOK_DISPATCH_SOURCE = HOOKS_ROOT / "common" / "hook_dispatch.py"
SHELL_COMMAND_INVOCATION_POSITION_SOURCE = (
    HOOKS_ROOT / "common" / "shell_command_invocation_position.py"
)
PROHIBITED_COMMAND_GUARD_SOURCE = next(HOOKS_ROOT.rglob("prohibited-command-guard.py"))
PROHIBITED_COMMAND_GUARD_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("prohibited_command_guard_handler.py")
)
PROHIBITED_WORDS_GUARD_SOURCE = next(HOOKS_ROOT.rglob("prohibited-words-guard.py"))
PROHIBITED_WORDS_GUARD_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("prohibited_words_guard_handler.py")
)
PROHIBITED_WORDS_SEGMENTS_SOURCE = next(
    HOOKS_ROOT.rglob("prohibited_words_segments.py")
)

COMMAND_GUARD_RUNTIME_SOURCES = [
    PROHIBITED_COMMAND_GUARD_SOURCE,
    PROHIBITED_COMMAND_GUARD_HANDLER_SOURCE,
    CODEX_TOOL_PAYLOAD_SOURCE,
    PRE_TOOL_USE_BLOCK_SOURCE,
    HOOK_DISPATCH_SOURCE,
    SHELL_COMMAND_INVOCATION_POSITION_SOURCE,
]

WORDS_GUARD_RUNTIME_SOURCES = [
    PROHIBITED_WORDS_GUARD_SOURCE,
    PROHIBITED_WORDS_GUARD_HANDLER_SOURCE,
    PROHIBITED_WORDS_SEGMENTS_SOURCE,
    CHANGED_FILE_PATHS_SOURCE,
    CODEX_TOOL_PAYLOAD_SOURCE,
    PRE_TOOL_USE_BLOCK_SOURCE,
    HOOK_DISPATCH_SOURCE,
    SHELL_COMMAND_INVOCATION_POSITION_SOURCE,
]


def flatten_into_single_runtime_directory(directory, source_files):
    for source_file in source_files:
        shutil.copy(source_file, directory / source_file.name)


def run_flattened_hook(directory, hook_filename, payload, environment=None):
    return subprocess.run(
        [sys.executable, str(directory / hook_filename)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
        env=environment if environment is not None else {**os.environ},
    )
