from pathlib import Path
from unittest.mock import patch

import theme_bg_next


class TestCollectSortedBackgroundFiles:
    def test_collects_files_from_theme_backgrounds(self, tmp_path):
        theme_dir = (
            tmp_path / ".config" / "hypr-theme" / "current" / "theme" / "backgrounds"
        )
        theme_dir.mkdir(parents=True)
        (theme_dir / "bg1.png").touch()
        (theme_dir / "bg2.jpg").touch()

        with patch.object(Path, "home", return_value=tmp_path):
            result = theme_bg_next.collect_sorted_background_files("test-theme")

        assert len(result) == 2

    def test_collects_files_from_user_backgrounds(self, tmp_path):
        user_dir = tmp_path / ".config" / "hypr-theme" / "backgrounds" / "my-theme"
        user_dir.mkdir(parents=True)
        (user_dir / "custom.png").touch()

        with patch.object(Path, "home", return_value=tmp_path):
            result = theme_bg_next.collect_sorted_background_files("my-theme")

        assert len(result) == 1
        assert result[0].name == "custom.png"

    def test_returns_empty_when_no_background_directories(self, tmp_path):
        with patch.object(Path, "home", return_value=tmp_path):
            result = theme_bg_next.collect_sorted_background_files("nonexistent")

        assert result == []

    def test_returns_sorted_by_path(self, tmp_path):
        theme_dir = (
            tmp_path / ".config" / "hypr-theme" / "current" / "theme" / "backgrounds"
        )
        theme_dir.mkdir(parents=True)
        (theme_dir / "c.png").touch()
        (theme_dir / "a.png").touch()
        (theme_dir / "b.png").touch()

        with patch.object(Path, "home", return_value=tmp_path):
            result = theme_bg_next.collect_sorted_background_files("test")

        names = [p.name for p in result]
        assert names == sorted(names)

    def test_user_backgrounds_come_before_theme_backgrounds(self, tmp_path):
        theme_dir = (
            tmp_path / ".config" / "hypr-theme" / "current" / "theme" / "backgrounds"
        )
        theme_dir.mkdir(parents=True)
        (theme_dir / "theme-bg.png").touch()

        user_dir = tmp_path / ".config" / "hypr-theme" / "backgrounds" / "my-theme"
        user_dir.mkdir(parents=True)
        (user_dir / "user-bg.png").touch()

        with patch.object(Path, "home", return_value=tmp_path):
            result = theme_bg_next.collect_sorted_background_files("my-theme")

        assert len(result) == 2


class TestFindCurrentBackgroundIndex:
    def test_returns_negative_one_when_no_symlink(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", tmp_path / "bg")
        assert theme_bg_next.find_current_background_index([]) == -1

    def test_returns_index_of_matching_background(self, tmp_path, monkeypatch):
        bg1 = tmp_path / "bg1.png"
        bg2 = tmp_path / "bg2.png"
        bg1.touch()
        bg2.touch()

        link = tmp_path / "current-bg"
        link.symlink_to(bg2)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        assert theme_bg_next.find_current_background_index([bg1, bg2]) == 1

    def test_returns_negative_one_when_target_not_in_list(self, tmp_path, monkeypatch):
        bg1 = tmp_path / "bg1.png"
        other = tmp_path / "other.png"
        bg1.touch()
        other.touch()

        link = tmp_path / "current-bg"
        link.symlink_to(other)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        assert theme_bg_next.find_current_background_index([bg1]) == -1


class TestSelectNextBackground:
    def test_selects_first_when_no_current(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            theme_bg_next, "CURRENT_BACKGROUND_LINK", tmp_path / "nonexistent"
        )
        bg1 = tmp_path / "bg1.png"
        bg2 = tmp_path / "bg2.png"
        result = theme_bg_next.select_next_background([bg1, bg2])
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

        result = theme_bg_next.select_next_background([bg1, bg2, bg3])
        assert result == bg2

    def test_wraps_around_to_first(self, tmp_path, monkeypatch):
        bg1 = tmp_path / "bg1.png"
        bg2 = tmp_path / "bg2.png"
        bg1.touch()
        bg2.touch()

        link = tmp_path / "current-bg"
        link.symlink_to(bg2)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        result = theme_bg_next.select_next_background([bg1, bg2])
        assert result == bg1


class TestSetBackgroundSymlinkAndApply:
    def test_creates_symlink_and_calls_apply(self, tmp_path, monkeypatch):
        link = tmp_path / "background"
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        new_bg = tmp_path / "wallpaper.png"
        new_bg.touch()

        with patch("theme_bg_next.subprocess.run") as mock_run:
            theme_bg_next.set_background_symlink_and_apply(new_bg)

            assert link.is_symlink()
            assert link.readlink() == new_bg
            mock_run.assert_called_once_with(["hypr-theme-bg-apply"])

    def test_replaces_existing_symlink(self, tmp_path, monkeypatch):
        old_bg = tmp_path / "old.png"
        new_bg = tmp_path / "new.png"
        old_bg.touch()
        new_bg.touch()

        link = tmp_path / "background"
        link.symlink_to(old_bg)
        monkeypatch.setattr(theme_bg_next, "CURRENT_BACKGROUND_LINK", link)

        with patch("theme_bg_next.subprocess.run"):
            theme_bg_next.set_background_symlink_and_apply(new_bg)

            assert link.readlink() == new_bg


class TestShowNoBackgroundsFallback:
    def test_launches_black_bg_then_kills_old(self):
        with (
            patch("theme_bg_next.get_running_swaybg_pids", return_value=["9999"]),
            patch("theme_bg_next.subprocess.run") as mock_run,
            patch("theme_bg_next.time.sleep"),
            patch("theme_bg_next.kill_swaybg_pids") as mock_kill,
        ):
            theme_bg_next.show_no_backgrounds_fallback()

            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                ["notify-send", "No background was found for theme", "-t", "2000"]
            )
            mock_run.assert_any_call(
                [
                    "hyprctl",
                    "dispatch",
                    "exec",
                    "swaybg --color '#000000'",
                ],
                capture_output=True,
            )
            mock_kill.assert_called_once_with(["9999"])
