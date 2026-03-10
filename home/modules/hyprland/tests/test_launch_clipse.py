from unittest.mock import patch

import launch_clipse_with_workspace_group_restoration


class TestMain:
    def test_launches_kitty_with_clipse(self):
        with patch(
            "launch_clipse_with_workspace_group_restoration.subprocess.run"
        ) as mock_run:
            launch_clipse_with_workspace_group_restoration.main()
            mock_run.assert_called_once_with(
                [
                    "kitty",
                    "--class",
                    "clipse",
                    "--override",
                    "startup_session=none",
                    "--override",
                    "background_image=none",
                    "-e",
                    "clipse",
                ]
            )
