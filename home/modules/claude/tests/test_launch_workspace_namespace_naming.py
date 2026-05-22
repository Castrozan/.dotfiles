def test_namespace_directory_is_stable_for_same_path(
    tmp_path, workspace_launcher_module
):
    workspace_directory = tmp_path / "my-project"
    workspace_directory.mkdir()

    first_namespace_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory(
            workspace_directory
        )
    )
    second_namespace_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory(
            workspace_directory
        )
    )

    assert first_namespace_directory == second_namespace_directory


def test_namespace_directory_differs_for_different_paths(
    tmp_path, workspace_launcher_module
):
    first_workspace_directory = tmp_path / "project-a"
    second_workspace_directory = tmp_path / "project-b"
    first_workspace_directory.mkdir()
    second_workspace_directory.mkdir()

    first_namespace_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory(
            first_workspace_directory
        )
    )
    second_namespace_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory(
            second_workspace_directory
        )
    )

    assert first_namespace_directory != second_namespace_directory


def test_namespace_directory_uses_workspace_skill_namespace_prefix(
    tmp_path, workspace_launcher_module
):
    workspace_directory = tmp_path / "my-project"
    workspace_directory.mkdir()

    namespace_directory = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory(
            workspace_directory
        )
    )

    assert namespace_directory.name.startswith("claude-workspace-skills.")
    assert (
        namespace_directory.parent
        == workspace_launcher_module.WORKSPACE_SKILL_NAMESPACE_PARENT_DIRECTORY
    )
