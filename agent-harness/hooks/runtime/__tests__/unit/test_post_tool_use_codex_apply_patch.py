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


def make_directory_look_like_dotfiles_repository(root):
    (root / ".git").mkdir()
    marker = root / "agent-harness" / "hooks" / "runtime" / "nix-rebuild"
    marker.mkdir(parents=True)
    marker.joinpath("nix_file_location.py").write_text("")


def recorded_ledger_contents(tmp_path):
    ledger_files = list(tmp_path.glob("claude-nix-rebuild-ledger-*.txt"))
    return "\n".join(path.read_text() for path in ledger_files)


def test_a_changed_nix_file_is_recorded_silently_on_codex_apply_patch(tmp_path):
    make_directory_look_like_dotfiles_repository(tmp_path)
    codex_hooks_directory = (
        tmp_path / "agent-harness" / "hooks" / "integrations" / "codex"
    )
    codex_hooks_directory.mkdir(parents=True)
    codex_hooks_directory.joinpath("codex-hooks-configuration.nix").write_text("{}")
    patch = "*** Begin Patch\n*** Update File: agent-harness/hooks/integrations/codex/codex-hooks-configuration.nix\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "", (
        "the recorder speaks at Stop through the ledger, not at edit time; an "
        "edit-time emission is the per-file noise this replaced"
    )
    assert "codex-hooks-configuration.nix" in recorded_ledger_contents(tmp_path)


def test_nothing_is_recorded_when_the_nix_file_is_outside_the_dotfiles_repo(tmp_path):
    patch = "*** Begin Patch\n*** Update File: agent-harness/hooks/integrations/codex/codex-hooks-configuration.nix\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert recorded_ledger_contents(tmp_path) == ""


def test_nothing_is_recorded_when_no_nix_file_changed(tmp_path):
    make_directory_look_like_dotfiles_repository(tmp_path)
    patch = "*** Begin Patch\n*** Update File: app/main.py\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert recorded_ledger_contents(tmp_path) == ""


def test_auto_format_runs_on_codex_apply_patch(tmp_path):
    edited_file = tmp_path / "sample.py"
    edited_file.write_text("value = 1\n")
    patch = "*** Begin Patch\n*** Update File: sample.py\n*** End Patch"
    result = run_codex_post_tool_use_dispatcher(
        tmp_path, apply_patch_payload(patch, tmp_path)
    )

    assert result.returncode == 0
    assert edited_file.exists()
