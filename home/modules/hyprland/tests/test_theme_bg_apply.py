from unittest.mock import patch, MagicMock

import pytest

import theme_bg_apply


class TestReadCurrentlyLoadedWallpaperPath:
    def test_returns_first_loaded_wallpaper_path(self):
        mock_result = MagicMock()
        mock_result.stdout = "/home/user/wallpaper.png\n"

        with patch(
            "theme_bg_apply.subprocess.run", return_value=mock_result
        ) as mock_run:
            result = theme_bg_apply.read_currently_loaded_wallpaper_path()

            assert result == "/home/user/wallpaper.png"
            mock_run.assert_called_once_with(
                ["hyprctl", "hyprpaper", "listloaded"],
                capture_output=True,
                text=True,
            )

    def test_returns_none_when_no_wallpapers_loaded(self):
        mock_result = MagicMock()
        mock_result.stdout = "\n"

        with patch("theme_bg_apply.subprocess.run", return_value=mock_result):
            result = theme_bg_apply.read_currently_loaded_wallpaper_path()
            assert result is None


class TestApplyCurrentBackground:
    def test_exits_when_no_symlink(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            theme_bg_apply, "CURRENT_BACKGROUND_LINK", tmp_path / "background"
        )

        with patch("theme_bg_apply.subprocess.run"):
            with pytest.raises(SystemExit):
                theme_bg_apply.apply_current_background()

    def test_exits_when_symlink_target_missing(self, tmp_path, monkeypatch):
        bg_link = tmp_path / "background"
        bg_link.symlink_to(tmp_path / "nonexistent.png")
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        with patch("theme_bg_apply.subprocess.run"):
            with pytest.raises(SystemExit):
                theme_bg_apply.apply_current_background()

    def test_preloads_and_sets_wallpaper_via_hyprctl(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        mock_listloaded = MagicMock()
        mock_listloaded.stdout = "\n"

        with patch(
            "theme_bg_apply.subprocess.run", return_value=mock_listloaded
        ) as mock_run:
            theme_bg_apply.apply_current_background()

            resolved_path = str(bg_file)
            mock_run.assert_any_call(
                ["hyprctl", "hyprpaper", "listloaded"],
                capture_output=True,
                text=True,
            )
            mock_run.assert_any_call(
                ["hyprctl", "hyprpaper", "preload", resolved_path],
                capture_output=True,
            )
            mock_run.assert_any_call(
                ["hyprctl", "hyprpaper", "wallpaper", f",{resolved_path}"],
                capture_output=True,
            )

    def test_unloads_previous_wallpaper_when_different(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "new_wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        previous_path = "/home/user/old_wallpaper.png"
        mock_listloaded = MagicMock()
        mock_listloaded.stdout = f"{previous_path}\n"

        with patch(
            "theme_bg_apply.subprocess.run", return_value=mock_listloaded
        ) as mock_run:
            theme_bg_apply.apply_current_background()

            mock_run.assert_any_call(
                ["hyprctl", "hyprpaper", "unload", previous_path],
                capture_output=True,
            )

    def test_does_not_unload_when_same_wallpaper(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        mock_listloaded = MagicMock()
        mock_listloaded.stdout = f"{bg_file}\n"

        with patch(
            "theme_bg_apply.subprocess.run", return_value=mock_listloaded
        ) as mock_run:
            theme_bg_apply.apply_current_background()

            unload_calls = [
                c
                for c in mock_run.call_args_list
                if len(c.args) > 0 and len(c.args[0]) >= 4 and c.args[0][2] == "unload"
            ]
            assert len(unload_calls) == 0

    def test_notifies_when_no_symlink(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            theme_bg_apply, "CURRENT_BACKGROUND_LINK", tmp_path / "background"
        )

        with patch("theme_bg_apply.subprocess.run") as mock_run:
            with pytest.raises(SystemExit):
                theme_bg_apply.apply_current_background()

            mock_run.assert_called_once_with(
                ["notify-send", "No background symlink found", "-t", "2000"]
            )
