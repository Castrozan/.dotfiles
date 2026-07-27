import json
import os

from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)

CODEX_SURFACE_ARGUMENT = "--surface=codex"


def run_codex_post_tool_use_dispatcher(tmp_path, payload, environment=None):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    return run_flattened_hook(
        runtime_directory,
        "post-tool-use-dispatcher.py",
        payload,
        environment
        if environment is not None
        else {**os.environ, "TMPDIR": str(tmp_path)},
        (CODEX_SURFACE_ARGUMENT,),
    )


def apply_patch_payload(patch_text, working_directory):
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "shell",
        "cwd": str(working_directory),
        "tool_input": {"command": ["apply_patch", patch_text]},
    }


def test_nix_rebuild_trigger_fires_on_codex_apply_patch(tmp_path):
    patch = "*** Begin Patch\n*** Update File: home/base/codex/hooks/default.nix\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    emitted = json.loads(result.stdout)
    assert "default.nix" in emitted["hookSpecificOutput"]["additionalContext"]
    assert "MANDATORY" in emitted["systemMessage"]


def test_nix_rebuild_trigger_silent_when_no_nix_file_changed(tmp_path):
    patch = "*** Begin Patch\n*** Update File: app/main.py\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_auto_format_runs_on_codex_apply_patch(tmp_path):
    edited_file = tmp_path / "sample.py"
    edited_file.write_text("value = 1\n")
    patch = "*** Begin Patch\n*** Update File: sample.py\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    assert edited_file.exists()
