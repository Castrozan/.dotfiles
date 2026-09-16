import session_context_hyprland


class TestExtractVscodeProjectNameFromTitle:
    def test_standard_vscode_title_with_file_and_project(self):
        title = "flake.nix - dotfiles - Visual Studio Code"
        assert (
            session_context_hyprland.extract_vscode_project_name_from_title(title)
            == "dotfiles"
        )

    def test_vscode_title_with_only_project(self):
        title = "oauth - Visual Studio Code"
        assert (
            session_context_hyprland.extract_vscode_project_name_from_title(title)
            == "oauth"
        )

    def test_vscode_title_with_nested_dashes_in_filename(self):
        title = "my-config-file.yaml - my-project - Visual Studio Code"
        assert (
            session_context_hyprland.extract_vscode_project_name_from_title(title)
            == "my-project"
        )

    def test_non_vscode_title_truncated(self):
        title = "Some Random Window Title"
        result = session_context_hyprland.extract_vscode_project_name_from_title(title)
        assert result == "Some Random Window Title"

    def test_long_non_vscode_title_truncated_at_40_chars(self):
        title = "A" * 60
        result = session_context_hyprland.extract_vscode_project_name_from_title(title)
        assert len(result) == 40
