import toggle_group_for_all_workspace_windows as toggler


class TestMain:
    def test_does_nothing_on_empty_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder("activewindow", None)
        toggler.main()

    def test_ungroups_when_all_grouped(
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
        toggler.main()
        dispatch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if len(c[0][0]) > 1 and "togglegroup" in str(c[0][0])
        ]
        assert len(dispatch_calls) > 0
