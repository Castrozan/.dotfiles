import os

import pytest

import theme_set


class TestSetBackgroundSymlinkFromCurrentTheme:
    def test_sets_symlink_to_first_background(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "current" / "theme"
        backgrounds_dir = theme_path / "backgrounds"
        backgrounds_dir.mkdir(parents=True)
        (backgrounds_dir / "wallpaper.png").touch()

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)

        theme_set.set_background_symlink_from_current_theme()

        background_link = tmp_path / "current" / "background"
        assert background_link.is_symlink()
        assert background_link.readlink() == backgrounds_dir / "wallpaper.png"

    def test_picks_first_alphabetically_when_multiple(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "current" / "theme"
        backgrounds_dir = theme_path / "backgrounds"
        backgrounds_dir.mkdir(parents=True)
        (backgrounds_dir / "c.png").touch()
        (backgrounds_dir / "a.png").touch()
        (backgrounds_dir / "b.png").touch()

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)

        theme_set.set_background_symlink_from_current_theme()

        background_link = tmp_path / "current" / "background"
        assert background_link.readlink() == backgrounds_dir / "a.png"

    def test_replaces_existing_symlink(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "current" / "theme"
        backgrounds_dir = theme_path / "backgrounds"
        backgrounds_dir.mkdir(parents=True)
        (backgrounds_dir / "new.png").touch()

        background_link = tmp_path / "current" / "background"
        old_target = tmp_path / "old.png"
        old_target.touch()
        background_link.symlink_to(old_target)

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)

        theme_set.set_background_symlink_from_current_theme()

        assert background_link.readlink() == backgrounds_dir / "new.png"

    def test_does_nothing_when_no_backgrounds_directory(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "current" / "theme"
        theme_path.mkdir(parents=True)

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)

        theme_set.set_background_symlink_from_current_theme()

        background_link = tmp_path / "current" / "background"
        assert not background_link.exists()

    def test_does_nothing_when_backgrounds_directory_is_empty(
        self, tmp_path, monkeypatch
    ):
        theme_path = tmp_path / "current" / "theme"
        (theme_path / "backgrounds").mkdir(parents=True)

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)

        theme_set.set_background_symlink_from_current_theme()

        background_link = tmp_path / "current" / "background"
        assert not background_link.exists()


class TestTouchShellWatchedThemeFilesIfPresent:
    @pytest.mark.parametrize(
        "file_name", list(theme_set.SHELL_WATCHED_THEME_FILE_NAMES)
    )
    def test_touches_file_when_exists(self, tmp_path, monkeypatch, file_name):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        watched_file = theme_path / file_name
        watched_file.write_text("{}")
        os.utime(watched_file, (0, 0))

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)

        theme_set.touch_shell_watched_theme_files_if_present()

        assert os.path.getmtime(watched_file) > 0

    def test_does_nothing_when_files_missing(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        theme_set.touch_shell_watched_theme_files_if_present()

        assert list(theme_path.iterdir()) == []
