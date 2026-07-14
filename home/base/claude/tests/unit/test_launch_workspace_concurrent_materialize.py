import os
from pathlib import Path

import pytest


def test_materialize_survives_concurrent_removal_of_final_namespace_directory(
    tmp_path, monkeypatch, workspace_launcher_module
):
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        tmp_path / "namespace-parent",
    )
    workspace_search_root_directory = tmp_path / "workspace"
    for concurrently_discovered_skill_name in ("alpha", "beta", "gamma"):
        skill_source_directory = (
            workspace_search_root_directory / concurrently_discovered_skill_name
        )
        skill_source_directory.mkdir(parents=True)
        (skill_source_directory / "SKILL.md").write_text(
            f"---\nname: {concurrently_discovered_skill_name}\n---\n"
        )

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    final_namespace_directory = launch_plan.workspace_skill_namespace_directory

    original_ensure_directory_symlink = (
        workspace_launcher_module.ensure_directory_symlink
    )
    competing_launcher_removal_already_injected = {"done": False}

    def ensure_directory_symlink_with_competing_launcher_removal(
        target_path, source_path
    ):
        if not competing_launcher_removal_already_injected["done"]:
            competing_launcher_removal_already_injected["done"] = True
            workspace_launcher_module.remove_workspace_skill_namespace_directory_in_place(
                final_namespace_directory
            )
        original_ensure_directory_symlink(target_path, source_path)

    monkeypatch.setattr(
        workspace_launcher_module,
        "ensure_directory_symlink",
        ensure_directory_symlink_with_competing_launcher_removal,
    )

    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan, workspace_search_root_directory
    )

    assert competing_launcher_removal_already_injected["done"]
    workspace_claude_skills_directory = final_namespace_directory / ".claude" / "skills"
    assert (final_namespace_directory / ".source-cwd").read_text().strip() == str(
        workspace_search_root_directory.resolve()
    )
    for expected_skill_name in ("alpha", "beta", "gamma"):
        assert (workspace_claude_skills_directory / expected_skill_name).is_symlink()


def test_orphaned_staging_directory_from_dead_process_is_swept(
    tmp_path, monkeypatch, workspace_launcher_module
):
    workspace_skill_namespace_parent_directory = tmp_path / "namespace-parent"
    workspace_skill_namespace_parent_directory.mkdir()
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        workspace_skill_namespace_parent_directory,
    )
    abandoned_workspace_source_cwd = tmp_path / "abandoned-workspace"
    abandoned_workspace_source_cwd.mkdir()

    never_running_process_identifier = 2_147_483_646
    orphaned_staging_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_staging_directory(
            abandoned_workspace_source_cwd, never_running_process_identifier
        )
    )
    orphaned_staging_directory.mkdir()
    (orphaned_staging_directory / "leftover-skill").mkdir()

    live_process_identifier = os.getpid()
    live_staging_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_staging_directory(
            abandoned_workspace_source_cwd, live_process_identifier
        )
    )
    live_staging_directory.mkdir()

    workspace_launcher_module.sweep_orphaned_workspace_skill_namespace_staging_directories()

    assert not orphaned_staging_directory.exists()
    assert live_staging_directory.is_dir()


def test_swap_accepts_final_namespace_already_materialized_by_a_concurrent_winner(
    tmp_path, monkeypatch, workspace_launcher_module
):
    staging_directory = tmp_path / "staging"
    staging_directory.mkdir()
    (staging_directory / "losing-marker").write_text("discarded\n")
    final_directory = tmp_path / "final"

    def refuse_replace_because_concurrent_winner_already_materialized_final(
        source_path, destination_path
    ):
        concurrent_winner_final_directory = Path(destination_path)
        concurrent_winner_final_directory.mkdir(parents=True, exist_ok=True)
        (concurrent_winner_final_directory / "winning-marker").write_text("kept\n")
        raise OSError("Directory not empty")

    monkeypatch.setattr(
        workspace_launcher_module.os,
        "replace",
        refuse_replace_because_concurrent_winner_already_materialized_final,
    )

    workspace_launcher_module.swap_staging_into_final_namespace_accepting_concurrent_winner(
        staging_directory, final_directory
    )

    assert (final_directory / "winning-marker").read_text().strip() == "kept"


def test_swap_reraises_when_replace_fails_and_no_final_namespace_exists(
    tmp_path, monkeypatch, workspace_launcher_module
):
    staging_directory = tmp_path / "staging"
    staging_directory.mkdir()
    final_directory = tmp_path / "final"

    def fail_replace(source_path, destination_path):
        raise OSError("cross-device move rejected")

    monkeypatch.setattr(workspace_launcher_module.os, "replace", fail_replace)

    with pytest.raises(OSError):
        workspace_launcher_module.swap_staging_into_final_namespace_accepting_concurrent_winner(
            staging_directory, final_directory
        )


def test_process_probe_permission_error_is_treated_as_running(
    monkeypatch, workspace_launcher_module
):
    def raise_permission_error(probed_process_identifier, probe_signal_number):
        raise PermissionError

    monkeypatch.setattr(workspace_launcher_module.os, "kill", raise_permission_error)

    assert (
        workspace_launcher_module.is_process_identifier_currently_running(4242) is True
    )
