from unittest.mock import call, patch

import scrolling_direction_toggle as script


class TestGetCurrentScrollingDirection:
    def test_returns_recognized_value(self):
        with patch.object(
            script, "run_hyprctl_json", return_value={"str": "down", "set": True}
        ):
            assert script.get_current_scrolling_direction() == "down"

    def test_returns_default_for_unknown_value(self):
        with patch.object(script, "run_hyprctl_json", return_value={"str": "diagonal"}):
            assert script.get_current_scrolling_direction() == script.DEFAULT_DIRECTION

    def test_returns_default_when_getoption_unavailable(self):
        with patch.object(script, "run_hyprctl_json", return_value=None):
            assert script.get_current_scrolling_direction() == script.DEFAULT_DIRECTION


class TestApplyScrollingDirection:
    def test_sends_keyword_then_recalculates(self):
        with patch.object(script, "run_hyprctl") as mock_run:
            script.apply_scrolling_direction("down")
        assert mock_run.call_args_list == [
            call("keyword", "scrolling:direction", "down"),
            call("dispatch", "layoutmsg", "fit active"),
        ]


class TestToggleScrollingDirection:
    def test_flips_horizontal_to_vertical(self):
        with (
            patch.object(
                script, "run_hyprctl_json", return_value={"str": "right", "set": True}
            ),
            patch.object(script, "run_hyprctl") as mock_run,
        ):
            target = script.toggle_scrolling_direction()
        assert target == "down"
        assert mock_run.call_args_list == [
            call("keyword", "scrolling:direction", "down"),
            call("dispatch", "layoutmsg", "fit active"),
        ]

    def test_flips_vertical_to_horizontal(self):
        with (
            patch.object(
                script, "run_hyprctl_json", return_value={"str": "down", "set": True}
            ),
            patch.object(script, "run_hyprctl") as mock_run,
        ):
            target = script.toggle_scrolling_direction()
        assert target == "right"
        assert mock_run.call_args_list == [
            call("keyword", "scrolling:direction", "right"),
            call("dispatch", "layoutmsg", "fit active"),
        ]
