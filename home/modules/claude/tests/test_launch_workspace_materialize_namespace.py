def test_namespace_directory_carries_sentinel_and_skill_symlinks_under_claude_skills_subpath(
    tmp_path, monkeypatch, workspace_launcher_module
):
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        tmp_path / "namespace-parent",
    )
    workspace_search_root_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_search_root_directory / "alpha"
    alpha_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan, workspace_search_root_directory
    )

    workspace_skill_namespace_directory = (
        launch_plan.workspace_skill_namespace_directory
    )
    source_cwd_sentinel_file = workspace_skill_namespace_directory / ".source-cwd"
    assert source_cwd_sentinel_file.read_text().strip() == str(
        workspace_search_root_directory.resolve()
    )
    symlinked_alpha_skill = (
        workspace_skill_namespace_directory / ".claude" / "skills" / "alpha"
    )
    assert symlinked_alpha_skill.is_symlink()
    assert symlinked_alpha_skill.resolve() == alpha_skill_directory.resolve()


def test_second_launch_rewrites_namespace_directory_with_current_skill_set(
    tmp_path, monkeypatch, workspace_launcher_module
):
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        tmp_path / "namespace-parent",
    )
    workspace_search_root_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_search_root_directory / "alpha"
    alpha_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")

    first_launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        first_launch_plan, workspace_search_root_directory
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
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        second_launch_plan, workspace_search_root_directory
    )

    workspace_claude_skills_directory = (
        second_launch_plan.workspace_skill_namespace_directory / ".claude" / "skills"
    )
    assert (workspace_claude_skills_directory / "beta").is_symlink()
    assert not (workspace_claude_skills_directory / "alpha").exists()


def test_empty_skill_set_skips_namespace_directory_creation(
    tmp_path, monkeypatch, workspace_launcher_module
):
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        tmp_path / "namespace-parent",
    )
    workspace_search_root_directory = tmp_path / "workspace"
    workspace_search_root_directory.mkdir()

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan, workspace_search_root_directory
    )

    assert not launch_plan.workspace_skill_namespace_directory.exists()


def test_no_global_state_or_credentials_files_are_written_into_namespace(
    tmp_path, monkeypatch, workspace_launcher_module
):
    monkeypatch.setattr(
        workspace_launcher_module,
        "WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY",
        tmp_path / "namespace-parent",
    )
    workspace_search_root_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_search_root_directory / "alpha"
    alpha_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )
    workspace_launcher_module.materialize_workspace_skill_namespace_directory_on_disk(
        launch_plan, workspace_search_root_directory
    )

    workspace_skill_namespace_directory = (
        launch_plan.workspace_skill_namespace_directory
    )
    assert not (workspace_skill_namespace_directory / ".credentials.json").exists()
    assert not (workspace_skill_namespace_directory / ".claude.json").exists()
    assert not (workspace_skill_namespace_directory / "settings.json").exists()
