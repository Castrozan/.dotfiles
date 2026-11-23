from unittest.mock import patch

import summon_brave


class TestSummonOrLaunchBrave:
    @patch("summon_brave.os.execvp")
    def test_launches_brave_when_no_window_found(
        self, mock_execvp, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"id": 1})
        hyprctl_response_builder("clients", [])
        summon_brave.summon_or_launch_brave()
        mock_execvp.assert_called_once_with("brave", ["brave"])

    def test_focuses_window_on_same_workspace(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"id": 1})
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "brave-browser",
                    "address": "0xa",
                    "workspace": {"id": 1},
                }
            ],
        )
        summon_brave.summon_or_launch_brave()
        dispatch_calls = [
            c for c in mock_subprocess_run.call_args_list if "focuswindow" in str(c)
        ]
        assert len(dispatch_calls) > 0

    def test_moves_window_from_different_workspace(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"id": 1})
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "brave-browser",
                    "address": "0xa",
                    "workspace": {"id": 2},
                }
            ],
        )
        summon_brave.summon_or_launch_brave()
        move_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if "hypr-move-window-to-workspace" in str(c)
        ]
        assert len(move_calls) == 1
