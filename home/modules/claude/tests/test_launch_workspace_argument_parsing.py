import pytest


def test_from_flag_is_extracted_and_remaining_args_are_passed_through(
    workspace_launcher_module,
):
    parsed_arguments = (
        workspace_launcher_module.parse_workspace_claude_wrapper_arguments(
            ["--from", "/tmp/some-skill", "--print", "hello"]
        )
    )

    assert parsed_arguments.requested_skill_source_directories == ["/tmp/some-skill"]
    assert parsed_arguments.remaining_claude_arguments == ["--print", "hello"]


def test_double_dash_terminates_wrapper_argument_parsing(workspace_launcher_module):
    parsed_arguments = (
        workspace_launcher_module.parse_workspace_claude_wrapper_arguments(
            ["--print", "--", "--from", "/should/not/be/parsed"]
        )
    )

    assert parsed_arguments.requested_skill_source_directories == []
    assert parsed_arguments.remaining_claude_arguments == [
        "--print",
        "--from",
        "/should/not/be/parsed",
    ]


def test_resolve_requested_skill_source_directories_requires_skill_markdown(
    tmp_path, workspace_launcher_module
):
    missing_skill_markdown_directory = tmp_path / "without-skill-markdown"
    missing_skill_markdown_directory.mkdir()

    with pytest.raises(workspace_launcher_module.WorkspaceLaunchConfigurationError):
        workspace_launcher_module.resolve_requested_skill_source_directories(
            [str(missing_skill_markdown_directory)]
        )


def test_from_flag_without_value_raises(workspace_launcher_module):
    with pytest.raises(workspace_launcher_module.WorkspaceLaunchConfigurationError):
        workspace_launcher_module.parse_workspace_claude_wrapper_arguments(["--from"])
