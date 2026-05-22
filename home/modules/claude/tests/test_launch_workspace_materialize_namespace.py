def test_namespace_directory_carries_sentinel_and_skill_symlinks(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    workspace_search_root_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_search_root_directory / "alpha"
    alpha_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan,
        global_claude_skills_directory,
        workspace_search_root_directory,
    )

    workspace_skill_namespace_directory = (
        launch_plan.workspace_skill_namespace_directory
    )
    assert workspace_skill_namespace_directory.is_dir()
    source_cwd_sentinel_file = workspace_skill_namespace_directory / ".source-cwd"
    assert source_cwd_sentinel_file.read_text().strip() == str(
        workspace_search_root_directory.resolve()
    )
    symlinked_alpha_skill = workspace_skill_namespace_directory / "alpha"
    assert symlinked_alpha_skill.is_symlink()
    assert symlinked_alpha_skill.resolve() == alpha_skill_directory.resolve()


def test_second_launch_rewrites_namespace_directory_with_current_skill_set(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    workspace_search_root_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_search_root_directory / "alpha"
    alpha_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")

    first_launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        first_launch_plan,
        global_claude_skills_directory,
        workspace_search_root_directory,
    )

    beta_skill_directory_added_between_launches = (
        workspace_search_root_directory / "beta"
    )
    beta_skill_directory_added_between_launches.mkdir()
    (beta_skill_directory_added_between_launches / "SKILL.md").write_text(
        "---\nname: beta\n---\n"
    )
    (alpha_skill_directory / "SKILL.md").unlink()
    alpha_skill_directory.rmdir()

    second_launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        second_launch_plan,
        global_claude_skills_directory,
        workspace_search_root_directory,
    )

    workspace_skill_namespace_directory = (
        second_launch_plan.workspace_skill_namespace_directory
    )
    assert (workspace_skill_namespace_directory / "beta").is_symlink()
    assert not (workspace_skill_namespace_directory / "alpha").exists()


def test_empty_skill_set_skips_namespace_directory_creation(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    workspace_search_root_directory = tmp_path / "workspace"
    workspace_search_root_directory.mkdir()

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan,
        global_claude_skills_directory,
        workspace_search_root_directory,
    )

    assert not launch_plan.workspace_skill_namespace_directory.exists()


def test_non_workspace_skill_entries_in_global_skills_directory_are_untouched(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    global_claude_skills_directory.mkdir(parents=True)
    home_manager_managed_core_skill_directory = global_claude_skills_directory / "core"
    home_manager_managed_core_skill_directory.mkdir()
    (home_manager_managed_core_skill_directory / "SKILL.md").write_text(
        "---\nname: core\n---\n"
    )
    personal_skill_vault_target_directory = tmp_path / "vault" / "personal"
    personal_skill_vault_target_directory.mkdir(parents=True)
    (personal_skill_vault_target_directory / "SKILL.md").write_text(
        "---\nname: personal\n---\n"
    )
    home_manager_personal_skill_symlink = global_claude_skills_directory / "personal"
    home_manager_personal_skill_symlink.symlink_to(
        personal_skill_vault_target_directory
    )

    workspace_search_root_directory = tmp_path / "workspace"
    workspace_search_root_directory.mkdir()

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan,
        global_claude_skills_directory,
        workspace_search_root_directory,
    )

    assert home_manager_managed_core_skill_directory.is_dir()
    assert (home_manager_managed_core_skill_directory / "SKILL.md").is_file()
    assert home_manager_personal_skill_symlink.is_symlink()


def test_no_global_state_or_credentials_files_are_written_into_namespace(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "skills"
    workspace_search_root_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_search_root_directory / "alpha"
    alpha_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan,
        global_claude_skills_directory,
        workspace_search_root_directory,
    )

    workspace_skill_namespace_directory = (
        launch_plan.workspace_skill_namespace_directory
    )
    assert not (workspace_skill_namespace_directory / ".credentials.json").exists()
    assert not (workspace_skill_namespace_directory / ".claude.json").exists()
    assert not (workspace_skill_namespace_directory / "settings.json").exists()
