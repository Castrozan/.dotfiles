import json
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
CHANGED_FILE_PATHS_SOURCE = HOOKS_ROOT / "common" / "changed_file_paths.py"
FORMATTER_TABLE_SOURCE = next(HOOKS_ROOT.rglob("formatter_table_by_extension.py"))
AUTO_FORMAT_SOURCE = next(HOOKS_ROOT.rglob("auto-format.py"))
NIX_REBUILD_TRIGGER_SOURCE = next(HOOKS_ROOT.rglob("nix-rebuild-trigger.py"))


def flatten_into_single_runtime_directory(directory, source_files):
    for source_file in source_files:
        shutil.copy(source_file, directory / source_file.name)


def run_flattened_hook(directory, hook_filename, payload):
    return subprocess.run(
        [sys.executable, str(directory / hook_filename)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_nix_rebuild_trigger_fires_on_codex_apply_patch(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory, [CHANGED_FILE_PATHS_SOURCE, NIX_REBUILD_TRIGGER_SOURCE]
    )

    patch = "*** Begin Patch\n*** Update File: home/base/codex/hooks/default.nix\n*** End Patch"
    payload = {
        "tool_name": "shell",
        "cwd": str(tmp_path),
        "tool_input": {"command": ["apply_patch", patch]},
    }

    result = run_flattened_hook(runtime_directory, "nix-rebuild-trigger.py", payload)
    assert result.returncode == 0
    emitted = json.loads(result.stdout)
    assert "default.nix" in emitted["hookSpecificOutput"]["additionalContext"]
    assert "MANDATORY" in emitted["systemMessage"]


def test_nix_rebuild_trigger_silent_when_no_nix_file_changed(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory, [CHANGED_FILE_PATHS_SOURCE, NIX_REBUILD_TRIGGER_SOURCE]
    )

    patch = "*** Begin Patch\n*** Update File: app/main.py\n*** End Patch"
    payload = {
        "tool_name": "shell",
        "cwd": str(tmp_path),
        "tool_input": {"command": ["apply_patch", patch]},
    }

    result = run_flattened_hook(runtime_directory, "nix-rebuild-trigger.py", payload)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_auto_format_imports_shared_modules_on_codex_apply_patch(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        [CHANGED_FILE_PATHS_SOURCE, FORMATTER_TABLE_SOURCE, AUTO_FORMAT_SOURCE],
    )

    edited_file = tmp_path / "sample.py"
    edited_file.write_text("value = 1\n")
    patch = "*** Begin Patch\n*** Update File: sample.py\n*** End Patch"
    payload = {
        "tool_name": "shell",
        "cwd": str(tmp_path),
        "tool_input": {"command": ["apply_patch", patch]},
    }

    result = run_flattened_hook(runtime_directory, "auto-format.py", payload)
    assert result.returncode == 0
    assert edited_file.exists()
