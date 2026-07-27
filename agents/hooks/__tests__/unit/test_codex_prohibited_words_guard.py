import json
import os

from codex_guard_test_support import (
    permission_decision_of,
    run_codex_pre_tool_use_dispatcher,
)


def run_words_guard(tmp_path, payload):
    prohibited_words_file = tmp_path / "prohibited-words.txt"
    prohibited_words_file.write_text("supersecretword\n")
    return run_codex_pre_tool_use_dispatcher(
        tmp_path,
        payload,
        {
            **os.environ,
            "PROHIBITED_WORDS_FILE": str(prohibited_words_file),
            "PROHIBITED_WORDS_ALLOWED": "",
        },
    )


def apply_patch_payload(patch_text, target_directory):
    return {
        "tool_name": "apply_patch",
        "cwd": str(target_directory),
        "tool_input": {"command": patch_text},
    }


def test_words_guard_blocks_prohibited_word_in_codex_commit(tmp_path):
    result = run_words_guard(
        tmp_path,
        {
            "tool_name": "shell",
            "cwd": str(tmp_path),
            "tool_input": {"command": ["git", "commit", "-m", "add supersecretword"]},
        },
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "supersecretword" in blocked["systemMessage"]


def test_words_guard_blocks_prohibited_word_in_codex_apply_patch_body(tmp_path):
    patch = (
        "*** Begin Patch\n"
        "*** Add File: note.md\n"
        "+contains supersecretword here\n"
        "*** End Patch"
    )
    result = run_words_guard(tmp_path, apply_patch_payload(patch, tmp_path))
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
    result = run_words_guard(tmp_path, apply_patch_payload(patch, tmp_path))
    assert result.returncode == 0
    assert permission_decision_of(result) is None
