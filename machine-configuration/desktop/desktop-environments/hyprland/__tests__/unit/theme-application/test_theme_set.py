import pytest

import theme_set


class TestNormalizeThemeName:
    def test_strips_tags_and_normalizes_together(self):
        assert theme_set.normalize_theme_name("<span>Rose Pine</span>") == "rose-pine"


class TestFindThemeDirectory:
    def test_finds_in_user_themes(self, tmp_path, monkeypatch):
        user_dir = tmp_path / "user-themes"
        (user_dir / "catppuccin").mkdir(parents=True)

        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", user_dir)

        result = theme_set.find_theme_directory("catppuccin")
        assert result == user_dir / "catppuccin"


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
