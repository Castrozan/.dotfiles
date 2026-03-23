from unittest.mock import patch

import workspace_grouping as grouping


class TestAllTiledWindowsAreInSingleGroupOnWorkspace:
    def test_returns_true_when_all_grouped(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "address": "0xa",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": ["0xa", "0xb"],
                },
                {
                    "address": "0xb",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": ["0xa", "0xb"],
                },
            ],
        )
        assert grouping.all_tiled_windows_are_in_single_group_on_workspace(1)

    def test_returns_false_when_not_grouped(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "address": "0xa",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": [],
                },
                {
                    "address": "0xb",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": [],
                },
            ],
        )
        assert not grouping.all_tiled_windows_are_in_single_group_on_workspace(1)

    def test_returns_false_on_empty_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder("clients", [])
        assert not grouping.all_tiled_windows_are_in_single_group_on_workspace(1)

    def test_ignores_floating_windows(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "address": "0xa",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": ["0xa"],
                },
                {
                    "address": "0xb",
                    "workspace": {"id": 1},
                    "floating": True,
                    "grouped": [],
                },
            ],
        )
        assert grouping.all_tiled_windows_are_in_single_group_on_workspace(1)


class TestGetTiledWindowAddressesOnWorkspace:
    def test_returns_only_tiled_on_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {"address": "0xa", "workspace": {"id": 1}, "floating": False},
                {"address": "0xb", "workspace": {"id": 1}, "floating": True},
                {"address": "0xc", "workspace": {"id": 2}, "floating": False},
            ],
        )
        result = grouping.get_tiled_window_addresses_on_workspace(1)
        assert result == ["0xa"]


class TestEnsureFirstWindowStartsGroup:
    def test_creates_group_when_ungrouped(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "clients",
            [{"address": "0xa", "workspace": {"id": 1}, "grouped": []}],
        )
        grouping.ensure_first_window_starts_group("0xa")
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert len(batch_calls) == 1
        assert "togglegroup" in str(batch_calls[0])

    def test_unlocks_existing_solo_group(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "clients",
            [{"address": "0xa", "workspace": {"id": 1}, "grouped": ["0xa"]}],
        )
        grouping.ensure_first_window_starts_group("0xa")
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert len(batch_calls) == 1
        assert "lockactivegroup unlock" in str(batch_calls[0])
        assert "togglegroup" not in str(batch_calls[0])

    def test_moves_out_of_existing_group_first(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "address": "0xa",
                    "workspace": {"id": 1},
                    "grouped": ["0xa", "0xother"],
                }
            ],
        )
        grouping.ensure_first_window_starts_group("0xa")
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert "moveoutofgroup" in str(batch_calls[0])


class TestDissolveAndMoveIntoTargetGroup:
    def test_moves_ungrouped_window_into_group(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "clients",
            [{"address": "0xb", "workspace": {"id": 1}, "grouped": []}],
        )
        grouping.dissolve_and_move_into_target_group("0xb")
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert "moveintogroup" in str(batch_calls[0])
        assert "togglegroup" not in str(batch_calls[0])

    def test_dissolves_solo_group_before_merge(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "clients",
            [{"address": "0xb", "workspace": {"id": 1}, "grouped": ["0xb"]}],
        )
        grouping.dissolve_and_move_into_target_group("0xb")
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert "togglegroup" in str(batch_calls[0])
        assert "moveintogroup" in str(batch_calls[0])


class TestGroupAllTiledWindowsAndMaximize:
    @patch("workspace_grouping.time.sleep")
    def test_maximizes_single_window(
        self, mock_sleep, mock_subprocess_run, hyprctl_response_builder
    ):
        grouping.group_all_tiled_windows_and_maximize(["0xa"])
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert "fullscreen 1 set" in str(batch_calls[0])

    @patch("workspace_grouping.time.sleep")
    def test_groups_multiple_windows(
        self, mock_sleep, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "clients",
            [
                {"address": "0xa", "workspace": {"id": 1}, "grouped": []},
                {"address": "0xb", "workspace": {"id": 1}, "grouped": []},
            ],
        )
        grouping.group_all_tiled_windows_and_maximize(["0xa", "0xb"])
        all_batch_commands = " ".join(
            str(c)
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        )
        assert "togglegroup" in all_batch_commands
        assert "moveintogroup" in all_batch_commands
