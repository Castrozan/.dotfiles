import all_tiled_windows_are_in_single_group as script


class TestAllTiledWindowsOnActiveWorkspaceAreInSingleGroup:
    def test_returns_true_when_all_tiled_are_grouped(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder(
            "activewindow", {"address": "0xaaa", "workspace": {"id": 1}}
        )
        hyprctl_response_builder("clients", sample_hyprland_clients)
        assert (
            script.all_tiled_windows_on_active_workspace_are_in_single_group() is True
        )

    def test_returns_false_when_not_all_grouped(self, hyprctl_response_builder):
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
        assert (
            script.all_tiled_windows_on_active_workspace_are_in_single_group() is False
        )

    def test_returns_false_when_no_tiled_windows(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow", {"address": "0xa", "workspace": {"id": 1}}
        )
        hyprctl_response_builder(
            "clients",
            [
                {
                    "address": "0xa",
                    "workspace": {"id": 1},
                    "floating": True,
                    "grouped": [],
                },
            ],
        )
        assert (
            script.all_tiled_windows_on_active_workspace_are_in_single_group() is False
        )

    def test_returns_false_when_no_active_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder("activewindow", None)
        assert (
            script.all_tiled_windows_on_active_workspace_are_in_single_group() is False
        )
