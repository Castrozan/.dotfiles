from unittest.mock import patch

import launch_clipse


class TestMain:
    def test_launches_wezterm_with_clipse(self):
        with patch("launch_clipse.subprocess.run") as mock_run:
            launch_clipse.main()
            mock_run.assert_called_once_with(
                [
                    "wezterm",
                    "start",
                    "--",
                    "clipse",
                ]
            )
