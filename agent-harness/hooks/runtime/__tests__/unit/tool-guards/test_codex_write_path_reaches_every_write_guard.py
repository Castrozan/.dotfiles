import json

from test_post_tool_use_codex_apply_patch import (
    apply_patch_payload,
    run_codex_post_tool_use_dispatcher,
)


def test_line_count_guard_blocks_an_over_threshold_codex_apply_patch(tmp_path):
    over_threshold_file = tmp_path / "too_long.py"
    over_threshold_file.write_text("\n".join(f"line_{n}" for n in range(250)) + "\n")

    patch = "*** Begin Patch\n*** Update File: too_long.py\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    emitted = json.loads(result.stdout)
    assert emitted["decision"] == "block"
    assert "too_long.py" in emitted["reason"]


def test_line_count_guard_allows_a_short_codex_apply_patch(tmp_path):
    short_file = tmp_path / "short.py"
    short_file.write_text("value = 1\n")

    patch = "*** Begin Patch\n*** Update File: short.py\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    emitted = json.loads(result.stdout) if result.stdout.strip() else {}
    assert emitted.get("decision") != "block"
