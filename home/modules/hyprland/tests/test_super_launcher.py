from unittest.mock import MagicMock, patch

import super_launcher


class TestIsFuzzelRunning:
    def test_returns_true_when_fuzzel_is_running(self):
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("super_launcher.subprocess.run", return_value=mock_result):
            assert super_launcher.is_fuzzel_running() is True

    def test_returns_false_when_fuzzel_is_not_running(self):
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("super_launcher.subprocess.run", return_value=mock_result):
            assert super_launcher.is_fuzzel_running() is False


class TestMain:
    def test_kills_fuzzel_when_already_running(self):
        with patch("super_launcher.is_fuzzel_running", return_value=True):
            with patch("super_launcher.subprocess.run") as mock_run:
                super_launcher.main()
                mock_run.assert_called_once_with(["pkill", "-x", "fuzzel"])

    def test_launches_fuzzel_when_not_running(self):
        with patch("super_launcher.is_fuzzel_running", return_value=False):
            with patch("super_launcher.subprocess.run") as mock_run:
                super_launcher.main()
                mock_run.assert_called_once_with(["hypr-fuzzel"])
