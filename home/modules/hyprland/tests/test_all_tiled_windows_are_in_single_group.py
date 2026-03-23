import all_tiled_windows_are_in_single_group as script


class TestMain:
    def test_exits_zero_when_all_tiled_are_grouped(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder(
            "activewindow", {"address": "0xaaa", "workspace": {"id": 1}}
        )
        hyprctl_response_builder("clients", sample_hyprland_clients)
        import sys
        from unittest.mock import patch

        with patch.object(sys, "exit") as mock_exit:
            script.main()
            mock_exit.assert_called_once_with(0)

    def test_exits_one_when_not_all_grouped(self, hyprctl_response_builder):
        clients = [
            {
                "address": "0xa",
                "workspace": {"id": 1},
                "floating": False,
                "grouped": ["0xa"],
            },
            {
                "address": "0xb",
                "workspace": {"id": 1},
                "floating": False,
                "grouped": ["0xb"],
            },
        ]
        hyprctl_response_builder(
            "activewindow", {"address": "0xa", "workspace": {"id": 1}}
        )
        hyprctl_response_builder("clients", clients)
        import sys
        from unittest.mock import patch

        with patch.object(sys, "exit") as mock_exit:
            script.main()
            mock_exit.assert_called_once_with(1)

    def test_exits_one_when_no_active_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder("activewindow", None)
        import sys
        from unittest.mock import patch

        with patch.object(sys, "exit") as mock_exit:
            script.main()
            mock_exit.assert_called_once_with(1)
