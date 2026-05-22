def test_namespace_directory_lives_under_global_skills_directory(
    tmp_path, workspace_launcher_module
):
    global_claude_skills_directory = tmp_path / "global-claude" / "skills"
    workspace_search_root_directory = tmp_path / "workspace"
    workspace_search_root_directory.mkdir()

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=global_claude_skills_directory,
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )

    expected_namespace_directory_name = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory_name(
            workspace_search_root_directory
        )
    )
    assert launch_plan.workspace_skill_namespace_directory == (
        global_claude_skills_directory / expected_namespace_directory_name
    )
    assert launch_plan.command_arguments == ["/bin/claude"]


def test_local_skill_discovery_populates_name_map(tmp_path, workspace_launcher_module):
    workspace_search_root_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_search_root_directory / "alpha"
    beta_skill_directory = workspace_search_root_directory / "nested" / "beta"
    alpha_skill_directory.mkdir(parents=True)
    beta_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")
    (beta_skill_directory / "SKILL.md").write_text("---\nname: beta\n---\n")

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=tmp_path / "skills",
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )

    assert launch_plan.discovered_skill_directory_name_map == {
        "alpha": alpha_skill_directory.resolve(),
        "beta": beta_skill_directory.resolve(),
    }


def test_requested_skill_directories_override_discovery(
    tmp_path, workspace_launcher_module
):
    workspace_search_root_directory = tmp_path / "workspace"
    ignored_discovered_skill_directory = workspace_search_root_directory / "discovered"
    ignored_discovered_skill_directory.mkdir(parents=True)
    (ignored_discovered_skill_directory / "SKILL.md").write_text(
        "---\nname: discovered\n---\n"
    )
    explicitly_requested_skill_directory = tmp_path / "explicit-skill"
    explicitly_requested_skill_directory.mkdir()
    (explicitly_requested_skill_directory / "SKILL.md").write_text(
        "---\nname: explicit\n---\n"
    )

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=tmp_path / "skills",
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[str(explicitly_requested_skill_directory)],
        claude_binary_path="/bin/claude",
    )

    assert launch_plan.discovered_skill_directory_name_map == {
        "explicit-skill": explicitly_requested_skill_directory.resolve(),
    }


def test_duplicate_local_skill_directory_names_keep_the_shallowest(
    tmp_path, workspace_launcher_module
):
    workspace_search_root_directory = tmp_path / "workspace"
    preferred_browser_skill_directory = (
        workspace_search_root_directory / "agents" / "skills" / "browser"
    )
    preferred_browser_skill_directory.mkdir(parents=True)
    (preferred_browser_skill_directory / "SKILL.md").write_text(
        "---\nname: browser\n---\n"
    )
    duplicate_browser_skill_directory_in_deeper_worktree = (
        workspace_search_root_directory
        / ".worktrees"
        / "branch-a"
        / "agents"
        / "skills"
        / "browser"
    )
    duplicate_browser_skill_directory_in_deeper_worktree.mkdir(parents=True)
    (duplicate_browser_skill_directory_in_deeper_worktree / "SKILL.md").write_text(
        "---\nname: browser-duplicate\n---\n"
    )

    launch_plan = workspace_launcher_module.prepare_workspace_claude_launch_plan(
        global_claude_skills_directory=tmp_path / "skills",
        workspace_search_root_directory=workspace_search_root_directory,
        requested_skill_source_directories=[],
        claude_binary_path="/bin/claude",
    )

    assert launch_plan.discovered_skill_directory_name_map == {
        "browser": preferred_browser_skill_directory.resolve(),
    }
