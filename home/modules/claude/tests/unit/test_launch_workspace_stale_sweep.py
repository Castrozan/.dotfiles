def test_namespace_directory_with_missing_source_cwd_is_swept(
    tmp_path, monkeypatch, workspace_launcher_module
):
    workspace_skill_namespace_parent_directory = tmp_path / "namespace-parent"
    workspace_skill_namespace_parent_directory.mkdir()
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        workspace_skill_namespace_parent_directory,
    )

    never_existed_source_cwd = tmp_path / "deleted-workspace"
    stale_namespace_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory(
            never_existed_source_cwd
        )
    )
    stale_namespace_directory.mkdir()
    (stale_namespace_directory / ".source-cwd").write_text(
        str(never_existed_source_cwd.resolve()) + "\n"
    )

    workspace_launcher_module.sweep_stale_workspace_skill_namespace_directories()

    assert not stale_namespace_directory.exists()


def test_namespace_directory_without_sentinel_is_swept(
    tmp_path, monkeypatch, workspace_launcher_module
):
    workspace_skill_namespace_parent_directory = tmp_path / "namespace-parent"
    workspace_skill_namespace_parent_directory.mkdir()
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        workspace_skill_namespace_parent_directory,
    )
    orphaned_namespace_directory_without_sentinel = (
        workspace_skill_namespace_parent_directory
        / "claude-workspace-skills.orphannosent"
    )
    orphaned_namespace_directory_without_sentinel.mkdir()
    (orphaned_namespace_directory_without_sentinel / "leftover-skill").mkdir()

    workspace_launcher_module.sweep_stale_workspace_skill_namespace_directories()

    assert not orphaned_namespace_directory_without_sentinel.exists()


def test_sweep_does_not_remove_unrelated_entries_in_parent_directory(
    tmp_path, monkeypatch, workspace_launcher_module
):
    workspace_skill_namespace_parent_directory = tmp_path / "namespace-parent"
    workspace_skill_namespace_parent_directory.mkdir()
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        workspace_skill_namespace_parent_directory,
    )
    unrelated_directory_in_parent_directory = (
        workspace_skill_namespace_parent_directory / "some-other-tool-cache"
    )
    unrelated_directory_in_parent_directory.mkdir()
    unrelated_symlink_in_parent_directory = (
        workspace_skill_namespace_parent_directory / "symlink-to-something"
    )
    unrelated_symlink_in_parent_directory.symlink_to(tmp_path / "anything")

    workspace_launcher_module.sweep_stale_workspace_skill_namespace_directories()

    assert unrelated_directory_in_parent_directory.is_dir()
    assert unrelated_symlink_in_parent_directory.is_symlink()


def test_sweep_keeps_namespace_directory_when_source_cwd_still_exists(
    tmp_path, monkeypatch, workspace_launcher_module
):
    workspace_skill_namespace_parent_directory = tmp_path / "namespace-parent"
    workspace_skill_namespace_parent_directory.mkdir()
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        workspace_skill_namespace_parent_directory,
    )
    surviving_source_cwd = tmp_path / "surviving-workspace"
    surviving_source_cwd.mkdir()
    surviving_namespace_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory(
            surviving_source_cwd
        )
    )
    surviving_namespace_directory.mkdir()
    (surviving_namespace_directory / ".source-cwd").write_text(
        str(surviving_source_cwd.resolve()) + "\n"
    )

    workspace_launcher_module.sweep_stale_workspace_skill_namespace_directories()

    assert surviving_namespace_directory.is_dir()
