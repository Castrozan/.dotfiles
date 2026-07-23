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
PROHIBITED_COMMAND_GUARD_SOURCE = next(HOOKS_ROOT.rglob("prohibited-command-guard.py"))
PROHIBITED_WORDS_GUARD_SOURCE = next(HOOKS_ROOT.rglob("prohibited-words-guard.py"))
PROHIBITED_WORDS_SEGMENTS_SOURCE = next(
    HOOKS_ROOT.rglob("prohibited_words_segments.py")
)

COMMAND_GUARD_RUNTIME_SOURCES = [
    PROHIBITED_COMMAND_GUARD_SOURCE,
    CODEX_TOOL_PAYLOAD_SOURCE,
    PRE_TOOL_USE_BLOCK_SOURCE,
]

WORDS_GUARD_RUNTIME_SOURCES = [
    PROHIBITED_WORDS_GUARD_SOURCE,
    PROHIBITED_WORDS_SEGMENTS_SOURCE,
    CHANGED_FILE_PATHS_SOURCE,
    CODEX_TOOL_PAYLOAD_SOURCE,
    PRE_TOOL_USE_BLOCK_SOURCE,
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


def test_command_guard_blocks_codex_shell_git_add_all(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        COMMAND_GUARD_RUNTIME_SOURCES,
    )

    payload = {"tool_name": "shell", "tool_input": {"command": ["git", "add", "-A"]}}
    result = run_flattened_hook(
        runtime_directory, "prohibited-command-guard.py", payload
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "BLOCKED" in blocked["systemMessage"]


def test_command_guard_allows_codex_read_only_shell(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        COMMAND_GUARD_RUNTIME_SOURCES,
    )

    payload = {"tool_name": "shell", "tool_input": {"command": ["cat", "README.md"]}}
    result = run_flattened_hook(
        runtime_directory, "prohibited-command-guard.py", payload
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_words_guard_blocks_prohibited_word_in_codex_commit(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        WORDS_GUARD_RUNTIME_SOURCES,
    )
    prohibited_words_file = tmp_path / "prohibited-words.txt"
    prohibited_words_file.write_text("supersecretword\n")

    payload = {
        "tool_name": "shell",
        "cwd": str(tmp_path),
        "tool_input": {"command": ["git", "commit", "-m", "add supersecretword"]},
    }
    result = run_flattened_hook(
        runtime_directory,
        "prohibited-words-guard.py",
        payload,
        environment={
            **os.environ,
            "PROHIBITED_WORDS_FILE": str(prohibited_words_file),
            "PROHIBITED_WORDS_ALLOWED": "",
        },
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "supersecretword" in blocked["systemMessage"]


def run_words_guard_on_apply_patch(tmp_path, patch_text, target_directory):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        WORDS_GUARD_RUNTIME_SOURCES,
    )
    prohibited_words_file = tmp_path / "prohibited-words.txt"
    prohibited_words_file.write_text("supersecretword\n")

    payload = {
        "tool_name": "apply_patch",
        "cwd": str(target_directory),
        "tool_input": {"command": patch_text},
    }
    return run_flattened_hook(
        runtime_directory,
        "prohibited-words-guard.py",
        payload,
        environment={
            **os.environ,
            "PROHIBITED_WORDS_FILE": str(prohibited_words_file),
            "PROHIBITED_WORDS_ALLOWED": "",
        },
    )


def test_words_guard_blocks_prohibited_word_in_codex_apply_patch_body(tmp_path):
    patch = (
        "*** Begin Patch\n"
        "*** Add File: note.md\n"
        "+contains supersecretword here\n"
        "*** End Patch"
    )
    result = run_words_guard_on_apply_patch(tmp_path, patch, tmp_path)
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "supersecretword" in blocked["systemMessage"]


def test_words_guard_allows_prohibited_word_in_private_config_apply_patch(tmp_path):
    private_directory = tmp_path / "private-config"
    private_directory.mkdir()
    patch = (
        "*** Begin Patch\n"
        "*** Add File: private-config/note.md\n"
        "+contains supersecretword here\n"
        "*** End Patch"
    )
    result = run_words_guard_on_apply_patch(tmp_path, patch, tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
