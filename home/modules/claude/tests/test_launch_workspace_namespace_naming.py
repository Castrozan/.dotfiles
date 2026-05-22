def test_namespace_directory_name_is_stable_for_same_path(
    tmp_path, workspace_launcher_module
):
    workspace_directory = tmp_path / "my-project"
    workspace_directory.mkdir()

    first_namespace_directory_name = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory_name(
            workspace_directory
        )
    )
    second_namespace_directory_name = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory_name(
            workspace_directory
        )
    )

    assert first_namespace_directory_name == second_namespace_directory_name
    assert first_namespace_directory_name.startswith("__workspace_")
    assert first_namespace_directory_name.endswith("__")


def test_namespace_directory_name_differs_for_different_paths(
    tmp_path, workspace_launcher_module
):
    first_workspace_directory = tmp_path / "project-a"
    second_workspace_directory = tmp_path / "project-b"
    first_workspace_directory.mkdir()
    second_workspace_directory.mkdir()

    first_namespace_directory_name = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory_name(
            first_workspace_directory
        )
    )
    second_namespace_directory_name = (
        workspace_launcher_module.compute_workspace_skill_namespace_directory_name(
            second_workspace_directory
        )
    )

    assert first_namespace_directory_name != second_namespace_directory_name
