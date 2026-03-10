from unittest.mock import MagicMock, patch

import pytest

import theme_bg_apply


class TestGetRunningSwaybgPids:
    def test_returns_pids_when_swaybg_running(self):
        mock_result = MagicMock(returncode=0, stdout="1234\n5678\n")
        with patch("theme_bg_apply.subprocess.run", return_value=mock_result):
            pids = theme_bg_apply.get_running_swaybg_pids()
        assert pids == ["1234", "5678"]

    def test_returns_empty_when_no_swaybg(self):
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("theme_bg_apply.subprocess.run", return_value=mock_result):
            pids = theme_bg_apply.get_running_swaybg_pids()
        assert pids == []


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

    def test_launches_new_swaybg_before_killing_old(self, tmp_path, monkeypatch):
        bg_file = tmp_path / "wallpaper.png"
        bg_file.write_bytes(b"fake-png")
        bg_link = tmp_path / "background"
        bg_link.symlink_to(bg_file)
        monkeypatch.setattr(theme_bg_apply, "CURRENT_BACKGROUND_LINK", bg_link)

        with (
            patch("theme_bg_apply.get_running_swaybg_pids", return_value=["1234"]),
            patch("theme_bg_apply.subprocess.run") as mock_run,
            patch("theme_bg_apply.time.sleep"),
            patch("theme_bg_apply.kill_swaybg_pids") as mock_kill,
        ):
            theme_bg_apply.apply_current_background()

            mock_run.assert_called_once_with(
                [
                    "hyprctl",
                    "dispatch",
                    "exec",
                    f"swaybg -i '{bg_link}' -m fill",
                ],
                capture_output=True,
            )
            mock_kill.assert_called_once_with(["1234"])

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
