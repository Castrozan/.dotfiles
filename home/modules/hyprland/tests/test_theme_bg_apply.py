from unittest.mock import patch

import pytest

import theme_bg_apply


class TestApplyCurrentBackground:
    """Uses swww instead of hyprpaper because hyprpaper cannot load GIF wallpapers."""
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

    def test_uses_swww_with_no_transition_for_quickshell_overlay(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        with patch("theme_bg_apply.subprocess.run") as mock_run:
            theme_bg_apply.apply_current_background()

            mock_run.assert_called_once_with(
                [
                    "swww", "img", str(bg_link),
                    "--resize", "crop",
                    "--transition-type", "none",
                ],
                capture_output=True,
            )

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
