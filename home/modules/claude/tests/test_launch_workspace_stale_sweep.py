def test_namespace_directory_with_missing_source_cwd_is_swept(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    global_claude_skills_directory.mkdir(parents=True)

    never_existed_source_cwd = tmp_path / "deleted-workspace"
    stale_namespace_directory_name = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory_name(
            never_existed_source_cwd
        )
    )
    stale_namespace_directory = (
        global_claude_skills_directory / stale_namespace_directory_name
    )
    stale_namespace_directory.mkdir()
    (stale_namespace_directory / ".source-cwd").write_text(
        str(never_existed_source_cwd.resolve()) + "\n"
    )

    surviving_workspace_search_root_directory = tmp_path / "surviving-workspace"
    surviving_workspace_search_root_directory.mkdir()
    surviving_alpha_skill_directory = (
        surviving_workspace_search_root_directory / "alpha"
    )
    surviving_alpha_skill_directory.mkdir()
    (surviving_alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=surviving_workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan,
        global_claude_skills_directory,
        surviving_workspace_search_root_directory,
    )

    assert not stale_namespace_directory.exists()
    assert launch_plan.workspace_skill_namespace_directory.exists()


def test_namespace_directory_without_sentinel_is_swept(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    global_claude_skills_directory.mkdir(parents=True)
    orphaned_namespace_directory_without_sentinel = (
        global_claude_skills_directory / "__workspace_orphannosent__"
    )
    orphaned_namespace_directory_without_sentinel.mkdir()
    (orphaned_namespace_directory_without_sentinel / "leftover-skill").mkdir()

    workspace_launcher_module.sweep_stale_workspace_skill_namespace_directories(
        global_claude_skills_directory
    )

    assert not orphaned_namespace_directory_without_sentinel.exists()


def test_sweep_does_not_remove_non_workspace_skill_entries(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    global_claude_skills_directory.mkdir(parents=True)
    home_manager_managed_core_skill_directory = global_claude_skills_directory / "core"
    home_manager_managed_core_skill_directory.mkdir()
    (home_manager_managed_core_skill_directory / "SKILL.md").write_text(
        "---\nname: core\n---\n"
    )
    plain_skill_symlink_target_directory = tmp_path / "elsewhere" / "skill"
    plain_skill_symlink_target_directory.mkdir(parents=True)
    plain_skill_symlink_in_global = global_claude_skills_directory / "elsewhere-skill"
    plain_skill_symlink_in_global.symlink_to(plain_skill_symlink_target_directory)

    workspace_launcher_module.sweep_stale_workspace_skill_namespace_directories(
        global_claude_skills_directory
    )

    assert home_manager_managed_core_skill_directory.is_dir()
    assert plain_skill_symlink_in_global.is_symlink()
