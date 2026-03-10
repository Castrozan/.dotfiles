import theme_list


class TestFormatThemeNameForDisplay:
    def test_capitalizes_single_word(self):
        assert theme_list.format_theme_name_for_display("catppuccin") == "Catppuccin"

    def test_capitalizes_hyphenated_words(self):
        assert (
            theme_list.format_theme_name_for_display("rose-pine-dawn")
            == "Rose Pine Dawn"
        )

    def test_handles_already_capitalized(self):
        assert theme_list.format_theme_name_for_display("Gruvbox") == "Gruvbox"


class TestCollectAllThemeNames:
    def test_collects_from_both_directories(self, tmp_path, monkeypatch):
        user_dir = tmp_path / "user-themes"
        hypr_dir = tmp_path / "hypr-themes"
        (user_dir / "custom-theme").mkdir(parents=True)
        (hypr_dir / "catppuccin").mkdir(parents=True)

        monkeypatch.setattr(theme_list, "USER_THEMES_PATH", user_dir)
        monkeypatch.setattr(theme_list, "HYPR_THEMES_PATH", hypr_dir)

        result = theme_list.collect_all_theme_names()
        assert result == ["catppuccin", "custom-theme"]

    def test_deduplicates_themes_present_in_both(self, tmp_path, monkeypatch):
        user_dir = tmp_path / "user-themes"
        hypr_dir = tmp_path / "hypr-themes"
        (user_dir / "catppuccin").mkdir(parents=True)
        (hypr_dir / "catppuccin").mkdir(parents=True)

        monkeypatch.setattr(theme_list, "USER_THEMES_PATH", user_dir)
        monkeypatch.setattr(theme_list, "HYPR_THEMES_PATH", hypr_dir)

        result = theme_list.collect_all_theme_names()
        assert result == ["catppuccin"]

    def test_ignores_files_only_includes_directories(self, tmp_path, monkeypatch):
        hypr_dir = tmp_path / "hypr-themes"
        hypr_dir.mkdir()
        (hypr_dir / "catppuccin").mkdir()
        (hypr_dir / "readme.txt").touch()

        monkeypatch.setattr(theme_list, "USER_THEMES_PATH", tmp_path / "missing")
        monkeypatch.setattr(theme_list, "HYPR_THEMES_PATH", hypr_dir)

        result = theme_list.collect_all_theme_names()
        assert result == ["catppuccin"]

    def test_returns_empty_when_no_directories_exist(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_list, "USER_THEMES_PATH", tmp_path / "a")
        monkeypatch.setattr(theme_list, "HYPR_THEMES_PATH", tmp_path / "b")

        result = theme_list.collect_all_theme_names()
        assert result == []

    def test_returns_sorted_names(self, tmp_path, monkeypatch):
        hypr_dir = tmp_path / "hypr-themes"
        (hypr_dir / "zenburn").mkdir(parents=True)
        (hypr_dir / "catppuccin").mkdir(parents=True)
        (hypr_dir / "kanagawa").mkdir(parents=True)

        monkeypatch.setattr(theme_list, "USER_THEMES_PATH", tmp_path / "missing")
        monkeypatch.setattr(theme_list, "HYPR_THEMES_PATH", hypr_dir)

        result = theme_list.collect_all_theme_names()
        assert result == ["catppuccin", "kanagawa", "zenburn"]
