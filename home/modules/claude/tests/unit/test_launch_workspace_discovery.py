def test_discovery_skips_pruned_child_directories(tmp_path, workspace_launcher_module):
    workspace_directory = tmp_path / "workspace"
    workspace_directory.mkdir()

    visible_skill_directory = workspace_directory / "visible-skill"
    visible_skill_directory.mkdir()
    (visible_skill_directory / "SKILL.md").write_text("---\nname: visible\n---\n")

    hidden_directory_with_skill = workspace_directory / ".hidden" / "buried-skill"
    hidden_directory_with_skill.mkdir(parents=True)
    (hidden_directory_with_skill / "SKILL.md").write_text("---\nname: buried\n---\n")

    node_modules_directory_with_skill = (
        workspace_directory / "node_modules" / "buried-package-skill"
    )
    node_modules_directory_with_skill.mkdir(parents=True)
    (node_modules_directory_with_skill / "SKILL.md").write_text(
        "---\nname: buried-package\n---\n"
    )

    discovered_skill_source_directories = (
        workspace_launcher_module.discover_workspace_skill_source_directories(
            workspace_directory
        )
    )

    assert discovered_skill_source_directories == [visible_skill_directory.resolve()]


def test_discovery_returns_empty_when_search_root_is_home_directory(
    tmp_path, monkeypatch, workspace_launcher_module
):
    fake_home_directory = tmp_path / "fake-home"
    fake_home_directory.mkdir()
    misleading_nested_skill_directory = fake_home_directory / "project" / "nested-skill"
    misleading_nested_skill_directory.mkdir(parents=True)
    (misleading_nested_skill_directory / "SKILL.md").write_text(
        "---\nname: nested\n---\n"
    )

    monkeypatch.setenv("HOME", str(fake_home_directory))

    discovered_skill_source_directories = (
        workspace_launcher_module.discover_workspace_skill_source_directories(
            fake_home_directory
        )
    )

    assert discovered_skill_source_directories == []
