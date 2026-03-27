from unittest.mock import patch

import launch_clipse_with_workspace_group_restoration


class TestMain:
    def test_launches_wezterm_with_clipse(self):
        with patch(
            "launch_clipse_with_workspace_group_restoration.subprocess.run"
        ) as mock_run:
            launch_clipse_with_workspace_group_restoration.main()
            mock_run.assert_called_once_with(
                [
                    "wezterm",
                    "start",
                    "--class",
                    "clipse",
                    "--",
                    "clipse",
                ]
            )
