import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
CODEX_TOOL_PAYLOAD_SOURCE = HOOKS_ROOT / "common" / "codex_tool_payload.py"
PROHIBITED_COMMAND_GUARD_SOURCE = next(HOOKS_ROOT.rglob("prohibited-command-guard.py"))
PROHIBITED_WORDS_GUARD_SOURCE = next(HOOKS_ROOT.rglob("prohibited-words-guard.py"))


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
        [PROHIBITED_COMMAND_GUARD_SOURCE, CODEX_TOOL_PAYLOAD_SOURCE],
    )

    payload = {"tool_name": "shell", "tool_input": {"command": ["git", "add", "-A"]}}
    result = run_flattened_hook(
        runtime_directory, "prohibited-command-guard.py", payload
    )
    assert result.returncode == 2
    assert "BLOCKED" in json.loads(result.stdout)["systemMessage"]


def test_command_guard_allows_codex_read_only_shell(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        [PROHIBITED_COMMAND_GUARD_SOURCE, CODEX_TOOL_PAYLOAD_SOURCE],
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
        [PROHIBITED_WORDS_GUARD_SOURCE, CODEX_TOOL_PAYLOAD_SOURCE],
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
    assert result.returncode == 2
    assert "supersecretword" in json.loads(result.stdout)["systemMessage"]
