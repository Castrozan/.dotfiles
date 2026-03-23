import ensure_workspace_tiled as script


class TestMain:
    def test_does_nothing_when_no_active_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder("activewindow", None)
        script.main()

    def test_does_nothing_when_not_grouped(
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
        dispatch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if len(c[0][0]) > 1 and "togglegroup" in str(c[0][0])
        ]
        assert len(dispatch_calls) == 0

    def test_dissolves_group_when_all_grouped(
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
        dispatch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if len(c[0][0]) > 1 and "togglegroup" in str(c[0][0])
        ]
        assert len(dispatch_calls) > 0

    def test_never_groups_ungrouped_windows(
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
                    "grouped": [],
                },
            ],
        )
        script.main()
        all_commands = " ".join(str(c) for c in mock_subprocess_run.call_args_list)
        assert "moveintogroup" not in all_commands
        assert "togglegroup" not in all_commands
