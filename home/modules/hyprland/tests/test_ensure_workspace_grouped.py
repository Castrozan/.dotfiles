from unittest.mock import patch

import ensure_workspace_grouped as script


class TestMain:
    def test_does_nothing_when_no_active_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder("activewindow", None)
        script.main()

    def test_does_nothing_when_already_grouped(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "activewindow", {"address": "0xa", "workspace": {"id": 1}}
        )
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
        script.main()
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert len(batch_calls) == 0

    @patch("workspace_grouping.time.sleep")
    def test_groups_ungrouped_windows(
        self, mock_sleep, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "activewindow", {"address": "0xa", "workspace": {"id": 1}}
        )
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
        script.main()
        all_batch_commands = " ".join(
            str(c)
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        )
        assert "moveintogroup" in all_batch_commands

    def test_never_dissolves_already_grouped_windows(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "activewindow", {"address": "0xa", "workspace": {"id": 1}}
        )
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
        script.main()
        all_commands = " ".join(str(c) for c in mock_subprocess_run.call_args_list)
        assert "togglegroup" not in all_commands

    def test_does_nothing_when_no_tiled_windows(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
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
        script.main()
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert len(batch_calls) == 0
