from unittest.mock import patch, MagicMock, call

import pytest

import theme_bg_apply


class TestReadCurrentlyLoadedWallpaperPath:
    def test_returns_first_loaded_wallpaper_path(self):
        with patch(
            "theme_bg_apply.send_hyprpaper_ipc_command",
            return_value="/home/user/wallpaper.png\n",
        ) as mock_ipc:
            result = theme_bg_apply.read_currently_loaded_wallpaper_path()

            assert result == "/home/user/wallpaper.png"
            mock_ipc.assert_called_once_with("listloaded")

    def test_returns_none_when_no_wallpapers_loaded(self):
        with patch("theme_bg_apply.send_hyprpaper_ipc_command", return_value="\n"):
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

    def test_preloads_and_sets_wallpaper_via_ipc(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        with patch(
            "theme_bg_apply.send_hyprpaper_ipc_command", return_value=""
        ) as mock_ipc:
            with patch(
                "theme_bg_apply.read_currently_loaded_wallpaper_path",
                return_value=None,
            ):
                theme_bg_apply.apply_current_background()

                resolved_path = str(bg_file)
                mock_ipc.assert_any_call(f"preload {resolved_path}")
                mock_ipc.assert_any_call(f"wallpaper ,{resolved_path}")

    def test_unloads_previous_wallpaper_when_different(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "new_wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        previous_path = "/home/user/old_wallpaper.png"

        with patch(
            "theme_bg_apply.send_hyprpaper_ipc_command", return_value=""
        ) as mock_ipc:
            with patch(
                "theme_bg_apply.read_currently_loaded_wallpaper_path",
                return_value=previous_path,
            ):
                theme_bg_apply.apply_current_background()

                mock_ipc.assert_any_call(f"unload {previous_path}")

    def test_does_not_unload_when_same_wallpaper(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        with patch(
            "theme_bg_apply.send_hyprpaper_ipc_command", return_value=""
        ) as mock_ipc:
            with patch(
                "theme_bg_apply.read_currently_loaded_wallpaper_path",
                return_value=str(bg_file),
            ):
                theme_bg_apply.apply_current_background()

                unload_calls = [
                    c
                    for c in mock_ipc.call_args_list
                    if str(c.args[0]).startswith("unload")
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
