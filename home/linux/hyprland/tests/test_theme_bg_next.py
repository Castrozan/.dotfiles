from unittest.mock import patch

import theme_bg_next


class TestCollectSortedWallpaperFiles:
    def test_collects_files_from_wallpapers_directory(self, tmp_path, monkeypatch):
        wallpapers_dir = tmp_path / "wallpapers"
        wallpapers_dir.mkdir(parents=True)
        (wallpapers_dir / "bg1.png").touch()
        (wallpapers_dir / "bg2.jpg").touch()

        monkeypatch.setattr(theme_bg_next, "WALLPAPERS_DIRECTORY", wallpapers_dir)

        result = theme_bg_next.collect_sorted_wallpaper_files()
        assert len(result) == 2

    def test_returns_empty_when_directory_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            theme_bg_next, "WALLPAPERS_DIRECTORY", tmp_path / "nonexistent"
        )

        result = theme_bg_next.collect_sorted_wallpaper_files()
        assert result == []

    def test_returns_sorted_by_path(self, tmp_path, monkeypatch):
        wallpapers_dir = tmp_path / "wallpapers"
        wallpapers_dir.mkdir(parents=True)
        (wallpapers_dir / "c.png").touch()
        (wallpapers_dir / "a.png").touch()
        (wallpapers_dir / "b.png").touch()

        monkeypatch.setattr(theme_bg_next, "WALLPAPERS_DIRECTORY", wallpapers_dir)

        result = theme_bg_next.collect_sorted_wallpaper_files()
        names = [p.name for p in result]
        assert names == sorted(names)

    def test_includes_symlinks(self, tmp_path, monkeypatch):
        wallpapers_dir = tmp_path / "wallpapers"
        wallpapers_dir.mkdir(parents=True)
        real_file = tmp_path / "real.png"
        real_file.touch()
        (wallpapers_dir / "link.png").symlink_to(real_file)

        monkeypatch.setattr(theme_bg_next, "WALLPAPERS_DIRECTORY", wallpapers_dir)

        result = theme_bg_next.collect_sorted_wallpaper_files()
        assert len(result) == 1
        assert result[0].name == "link.png"


class TestFindCurrentWallpaperIndex:
    def test_returns_negative_one_when_no_symlink(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", tmp_path / "bg")
        assert theme_bg_next.find_current_wallpaper_index([]) == -1

    def test_returns_index_of_matching_wallpaper(self, tmp_path, monkeypatch):
        bg1 = tmp_path / "bg1.png"
        bg2 = tmp_path / "bg2.png"
        bg1.touch()
        bg2.touch()

        link = tmp_path / "current-bg"
        link.symlink_to(bg2)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        assert theme_bg_next.find_current_wallpaper_index([bg1, bg2]) == 1

    def test_returns_negative_one_when_target_not_in_list(self, tmp_path, monkeypatch):
        bg1 = tmp_path / "bg1.png"
        other = tmp_path / "other.png"
        bg1.touch()
        other.touch()

        link = tmp_path / "current-bg"
        link.symlink_to(other)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        assert theme_bg_next.find_current_wallpaper_index([bg1]) == -1


class TestSelectNextWallpaper:
    def test_selects_first_when_no_current(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            theme_bg_next, "CURRENT_BACKGROUND_LINK", tmp_path / "nonexistent"
        )
        bg1 = tmp_path / "bg1.png"
        bg2 = tmp_path / "bg2.png"
        result = theme_bg_next.select_next_wallpaper([bg1, bg2])
        assert result == bg1

    def test_cycles_to_next(self, tmp_path, monkeypatch):
        bg1 = tmp_path / "bg1.png"
        bg2 = tmp_path / "bg2.png"
        bg3 = tmp_path / "bg3.png"
        bg1.touch()
        bg2.touch()
        bg3.touch()

        link = tmp_path / "current-bg"
        link.symlink_to(bg1)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        result = theme_bg_next.select_next_wallpaper([bg1, bg2, bg3])
        assert result == bg2

    def test_wraps_around_to_first(self, tmp_path, monkeypatch):
        bg1 = tmp_path / "bg1.png"
        bg2 = tmp_path / "bg2.png"
        bg1.touch()
        bg2.touch()

        link = tmp_path / "current-bg"
        link.symlink_to(bg2)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        result = theme_bg_next.select_next_wallpaper([bg1, bg2])
        assert result == bg1


class TestGenerateAndApplyThemeFromWallpaper:
    def test_calls_generate_and_apply_with_wallpaper_path(self, tmp_path):
        wallpaper = tmp_path / "wallpaper.png"
        wallpaper.touch()

        with patch("theme_bg_next.subprocess.run") as mock_run:
            theme_bg_next.generate_and_apply_theme_from_wallpaper(wallpaper)
            mock_run.assert_called_once_with(
                ["hypr-theme-generate-and-apply", str(wallpaper)]
            )


class TestShowNoWallpapersFallback:
    def test_sends_notification_and_clears_screen(self):
        with patch("theme_bg_next.subprocess.run") as mock_run:
            theme_bg_next.show_no_wallpapers_fallback()

            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                ["notify-send", "No wallpapers found", "-t", "2000"]
            )
            mock_run.assert_any_call(
                ["swww", "clear", "000000"],
                capture_output=True,
            )
