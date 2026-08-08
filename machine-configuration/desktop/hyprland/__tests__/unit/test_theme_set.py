import pytest

import theme_set


class TestNormalizeThemeName:
    def test_lowercases_and_replaces_spaces(self):
        assert theme_set.normalize_theme_name("Rose Pine Dawn") == "rose-pine-dawn"

    def test_strips_html_tags(self):
        assert theme_set.normalize_theme_name("<b>Catppuccin</b>") == "catppuccin"

    def test_handles_already_normalized(self):
        assert theme_set.normalize_theme_name("kanagawa") == "kanagawa"

    def test_strips_tags_and_normalizes_together(self):
        assert theme_set.normalize_theme_name("<span>Rose Pine</span>") == "rose-pine"


class TestFindThemeDirectory:
    def test_finds_in_user_themes(self, tmp_path, monkeypatch):
        user_dir = tmp_path / "user-themes"
        (user_dir / "catppuccin").mkdir(parents=True)

        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", user_dir)

        result = theme_set.find_theme_directory("catppuccin")
        assert result == user_dir / "catppuccin"

    def test_returns_none_when_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", tmp_path / "a")

        assert theme_set.find_theme_directory("nonexistent") is None


class TestMainExitsOnMissingArguments:
    def test_exits_with_no_args(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["theme_set"])
        with pytest.raises(SystemExit):
            theme_set.main()

    def test_exits_when_theme_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sys.argv", ["theme_set", "nonexistent"])
        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", tmp_path / "a")

        with pytest.raises(SystemExit):
            theme_set.main()
