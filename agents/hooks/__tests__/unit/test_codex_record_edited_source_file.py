import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOKS_ROOT = Path(__file__).resolve().parents[2]
CHANGED_FILE_PATHS_SOURCE = HOOKS_ROOT / "common" / "changed_file_paths.py"
HOOK_DISPATCH_SOURCE = HOOKS_ROOT / "common" / "hook_dispatch.py"
LINT_LEDGER_SOURCE = next(HOOKS_ROOT.rglob("lint_ledger.py"))
LINTER_TABLE_SOURCE = next(HOOKS_ROOT.rglob("linter_table_by_extension.py"))
RECORD_EDITED_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("record_edited_source_file_handler.py")
)
RECORD_EDITED_SOURCE = next(HOOKS_ROOT.rglob("record-edited-source-file.py"))


def flatten_into_single_runtime_directory(directory, source_files):
    for source_file in source_files:
        shutil.copy(source_file, directory / source_file.name)


def test_record_edited_logs_codex_apply_patch_nix_file(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        [
            CHANGED_FILE_PATHS_SOURCE,
            HOOK_DISPATCH_SOURCE,
            LINT_LEDGER_SOURCE,
            LINTER_TABLE_SOURCE,
            RECORD_EDITED_HANDLER_SOURCE,
            RECORD_EDITED_SOURCE,
        ],
    )

    edited_file = tmp_path / "module.nix"
    edited_file.write_text("{ }\n")
    patch = "*** Begin Patch\n*** Update File: module.nix\n*** End Patch"
    payload = {
        "session_id": "sessionone",
        "cwd": str(tmp_path),
        "tool_input": {"command": ["apply_patch", patch]},
    }

    ledger_directory = tmp_path / "ledger"
    ledger_directory.mkdir()
    result = subprocess.run(
        [sys.executable, str(runtime_directory / "record-edited-source-file.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        env={**os.environ, "TMPDIR": str(ledger_directory)},
    )

    assert result.returncode == 0
    ledger_file = ledger_directory / "claude-lint-ledger-sessionone.txt"
    assert ledger_file.exists()
    assert str(edited_file) in ledger_file.read_text()
