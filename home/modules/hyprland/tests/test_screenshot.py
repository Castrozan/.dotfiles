import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import screenshot


class TestGetScreenshotsDirectory:
    def test_uses_xdg_pictures_dir(self):
        with patch.dict("os.environ", {"XDG_PICTURES_DIR": "/custom/pics"}):
            result = screenshot.get_screenshots_directory()
            assert result == Path("/custom/pics/Screenshots")

    def test_falls_back_to_home_pictures(self, tmp_path):
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(Path, "home", return_value=tmp_path):
                result = screenshot.get_screenshots_directory()
                assert result == tmp_path / "Pictures" / "Screenshots"


class TestCaptureRegionScreenshot:
    def test_returns_false_when_slurp_cancelled(self, tmp_path):
        slurp_result = MagicMock()
        slurp_result.returncode = 1

        with patch("screenshot.subprocess.run", return_value=slurp_result):
            assert screenshot.capture_region_screenshot(tmp_path / "test.png") is False

    def test_captures_region_with_grim(self, tmp_path):
        slurp_result = MagicMock()
        slurp_result.returncode = 0
        slurp_result.stdout = "100,200 300x400"

        with patch("screenshot.subprocess.run") as mock_run:
            mock_run.return_value = slurp_result
            save_path = tmp_path / "test.png"
            result = screenshot.capture_region_screenshot(save_path)

            assert result is True
            assert mock_run.call_args_list[1] == call(
                ["grim", "-g", "100,200 300x400", str(save_path)]
            )


class TestCaptureActiveWindowScreenshot:
    def test_captures_window_geometry(self, tmp_path):
        window_json = json.dumps({"at": [100, 200], "size": [800, 600]})

        def run_side_effect(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "activewindow" in args:
                result.stdout = window_json
            return result

        with patch(
            "screenshot.subprocess.run", side_effect=run_side_effect
        ) as mock_run:
            save_path = tmp_path / "test.png"
            result = screenshot.capture_active_window_screenshot(save_path)
            assert result is True
            grim_call = mock_run.call_args_list[1]
            assert grim_call == call(["grim", "-g", "100,200 800x600", str(save_path)])


class TestCaptureFullScreenScreenshot:
    def test_calls_grim_without_geometry(self, tmp_path):
        with patch("screenshot.subprocess.run") as mock_run:
            save_path = tmp_path / "test.png"
            result = screenshot.capture_full_screen_screenshot(save_path)
            assert result is True
            mock_run.assert_called_once_with(["grim", str(save_path)])


class TestCopyScreenshotToClipboardAndNotify:
    def test_copies_to_clipboard_and_notifies(self, tmp_path):
        save_path = tmp_path / "test.png"
        save_path.write_bytes(b"fake png data")

        with patch("screenshot.subprocess.run") as mock_run:
            screenshot.copy_screenshot_to_clipboard_and_notify(save_path)

            wl_copy_call = mock_run.call_args_list[0]
            assert wl_copy_call[0][0] == ["wl-copy"]

            notify_call = mock_run.call_args_list[1]
            assert "notify-send" in notify_call[0][0]
            assert "Screenshot saved" in notify_call[0][0]


class TestMain:
    def test_region_mode_default(self, tmp_path):
        with patch(
            "screenshot.capture_region_screenshot", return_value=True
        ) as mock_capture:
            with patch("screenshot.copy_screenshot_to_clipboard_and_notify"):
                with patch("screenshot.sys.argv", ["cmd"]):
                    with patch(
                        "screenshot.get_screenshots_directory",
                        return_value=tmp_path,
                    ):
                        screenshot.main()
                        mock_capture.assert_called_once()

    def test_unknown_mode_exits(self):
        with patch("screenshot.sys.argv", ["cmd", "unknown"]):
            with patch(
                "screenshot.get_screenshots_directory",
                return_value=Path("/tmp"),
            ):
                try:
                    screenshot.main()
                    assert False, "Should have raised SystemExit"
                except SystemExit as e:
                    assert e.code == 1
