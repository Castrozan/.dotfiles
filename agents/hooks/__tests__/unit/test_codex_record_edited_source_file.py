import os

from test_post_tool_use_codex_apply_patch import (
    apply_patch_payload,
    run_codex_post_tool_use_dispatcher,
)


def test_record_edited_logs_codex_apply_patch_nix_file(tmp_path):
    edited_file = tmp_path / "module.nix"
    edited_file.write_text("{ }\n")
    ledger_directory = tmp_path / "ledger"
    ledger_directory.mkdir()

    patch = "*** Begin Patch\n*** Update File: module.nix\n*** End Patch"
    payload = {
        **apply_patch_payload(patch, tmp_path),
        "session_id": "sessionone",
    }
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, payload, {**os.environ, "TMPDIR": str(ledger_directory)}
    )

    assert result.returncode == 0
    ledger_file = ledger_directory / "claude-lint-ledger-sessionone.txt"
    assert ledger_file.exists()
    assert str(edited_file) in ledger_file.read_text()
