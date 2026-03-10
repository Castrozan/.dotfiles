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
    def test_finds_in_user_themes_first(self, tmp_path, monkeypatch):
        user_dir = tmp_path / "user-themes"
        hypr_dir = tmp_path / "hypr-themes"
        (user_dir / "catppuccin").mkdir(parents=True)
        (hypr_dir / "catppuccin").mkdir(parents=True)

        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", user_dir)
        monkeypatch.setattr(theme_set, "HYPR_THEMES_PATH", hypr_dir)

        result = theme_set.find_theme_directory("catppuccin")
        assert result == user_dir / "catppuccin"

    def test_finds_in_hypr_themes_when_not_in_user(self, tmp_path, monkeypatch):
        user_dir = tmp_path / "user-themes"
        hypr_dir = tmp_path / "hypr-themes"
        user_dir.mkdir()
        (hypr_dir / "kanagawa").mkdir(parents=True)

        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", user_dir)
        monkeypatch.setattr(theme_set, "HYPR_THEMES_PATH", hypr_dir)

        result = theme_set.find_theme_directory("kanagawa")
        assert result == hypr_dir / "kanagawa"

    def test_returns_none_when_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", tmp_path / "a")
        monkeypatch.setattr(theme_set, "HYPR_THEMES_PATH", tmp_path / "b")

        assert theme_set.find_theme_directory("nonexistent") is None


class TestCopyThemeToNextThemeDirectory:
    def test_copies_theme_directory(self, tmp_path, monkeypatch):
        source = tmp_path / "source-theme"
        source.mkdir()
        (source / "colors.toml").write_text('primary = "#ff0000"\n')
        (source / "bg").mkdir()
        (source / "bg" / "wallpaper.png").write_bytes(b"png")

        next_theme = tmp_path / "next-theme"
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.copy_theme_to_next_theme_directory(source)

        assert (next_theme / "colors.toml").read_text() == 'primary = "#ff0000"\n'
        assert (next_theme / "bg" / "wallpaper.png").read_bytes() == b"png"

    def test_removes_existing_next_theme_before_copy(self, tmp_path, monkeypatch):
        source = tmp_path / "source"
        source.mkdir()
        (source / "new.txt").write_text("new")

        next_theme = tmp_path / "next-theme"
        next_theme.mkdir()
        (next_theme / "old.txt").write_text("old")

        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.copy_theme_to_next_theme_directory(source)

        assert not (next_theme / "old.txt").exists()
        assert (next_theme / "new.txt").read_text() == "new"


class TestRotateCurrentThemeWithNext:
    def test_replaces_current_with_next(self, tmp_path, monkeypatch):
        current = tmp_path / "current" / "theme"
        current.mkdir(parents=True)
        (current / "old.txt").write_text("old")

        next_theme = tmp_path / "current" / "next-theme"
        next_theme.mkdir()
        (next_theme / "new.txt").write_text("new")

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", current)
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.rotate_current_theme_with_next()

        assert (current / "new.txt").read_text() == "new"
        assert not (current / "old.txt").exists()
        assert not next_theme.exists()

    def test_works_when_no_current_theme(self, tmp_path, monkeypatch):
        current = tmp_path / "current" / "theme"
        (tmp_path / "current").mkdir()

        next_theme = tmp_path / "current" / "next-theme"
        next_theme.mkdir()
        (next_theme / "file.txt").write_text("content")

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", current)
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.rotate_current_theme_with_next()

        assert (current / "file.txt").read_text() == "content"


class TestTouchQuickshellBarThemeColorsIfPresent:
    def test_touches_file_when_exists(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        colors_file = theme_path / "quickshell-bar-colors.json"
        colors_file.write_text("{}")

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)

        import os

        old_mtime = os.path.getmtime(colors_file)

        import time

        time.sleep(0.01)
        theme_set.touch_quickshell_bar_theme_colors_if_present()

        new_mtime = os.path.getmtime(colors_file)
        assert new_mtime >= old_mtime

    def test_does_nothing_when_file_missing(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        theme_set.touch_quickshell_bar_theme_colors_if_present()


class TestUpdateBtopThemeInConfig:
    def test_updates_color_theme_and_background(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        btop_theme = theme_path / "btop.theme"
        btop_theme.write_text("theme content")

        btop_conf = tmp_path / "btop.conf"
        btop_conf.write_text(
            'color_theme = "/old/path/theme"\n'
            "theme_background = True\n"
            "other_setting = value\n"
        )

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "BTOP_CONF", btop_conf)

        theme_set.update_btop_theme_in_config()

        content = btop_conf.read_text()
        assert f'color_theme = "{btop_theme}"' in content
        assert "theme_background = False" in content
        assert "other_setting = value" in content

    def test_does_nothing_when_no_btop_conf(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "btop.theme").write_text("theme")

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "BTOP_CONF", tmp_path / "nonexistent")

        theme_set.update_btop_theme_in_config()

    def test_does_nothing_when_no_btop_theme(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()

        btop_conf = tmp_path / "btop.conf"
        btop_conf.write_text('color_theme = "old"\n')

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "BTOP_CONF", btop_conf)

        theme_set.update_btop_theme_in_config()

        assert btop_conf.read_text() == 'color_theme = "old"\n'


class TestMainExitsOnMissingArguments:
    def test_exits_with_no_args(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["theme_set"])
        with pytest.raises(SystemExit):
            theme_set.main()

    def test_exits_when_theme_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sys.argv", ["theme_set", "nonexistent"])
        monkeypatch.setattr(theme_set, "USER_THEMES_PATH", tmp_path / "a")
        monkeypatch.setattr(theme_set, "HYPR_THEMES_PATH", tmp_path / "b")

        with pytest.raises(SystemExit):
            theme_set.main()
