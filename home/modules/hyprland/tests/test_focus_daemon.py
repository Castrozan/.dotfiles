from unittest.mock import patch

import focus_daemon as daemon


class TestDaemonState:
    def test_initial_state_has_empty_focus_tracking(self):
        state = daemon.DaemonState()
        assert state.current_focused_address == ""
        assert state.previous_focused_address == ""


class TestInitializeFocusedWindowTracking:
    def test_sets_current_focused_from_active_window(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow", {"address": "0xabc", "workspace": {"id": 1}}
        )
        state = daemon.DaemonState()
        daemon.initialize_focused_window_tracking(state)
        assert state.current_focused_address == "0xabc"
        assert state.previous_focused_address == ""


class TestHandleActiveWindowChangedEvent:
    def test_updates_focus_history(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        state = daemon.DaemonState(current_focused_address="0xold")
        daemon.handle_active_window_changed_event(state, "abc")
        assert state.current_focused_address == "0xabc"
        assert state.previous_focused_address == "0xold"

    def test_does_not_update_when_same_address(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        state = daemon.DaemonState(
            current_focused_address="0xabc",
            previous_focused_address="0xprev",
        )
        daemon.handle_active_window_changed_event(state, "abc")
        assert state.previous_focused_address == "0xprev"


class TestHandleActiveWindowChangedPinnedWindowSurvival:
    def test_pinned_floating_window_not_moved_offscreen_when_tiled_gets_focus(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        state = daemon.DaemonState(current_focused_address="0xeee")
        daemon.handle_active_window_changed_event(state, "aaa")
        all_offscreen_args = " ".join(
            str(c)
            for c in mock_subprocess_run.call_args_list
            if "movewindowpixel" in str(c)
        )
        assert "0xeee" not in all_offscreen_args

    def test_unpinned_floating_window_still_moved_offscreen_when_tiled_gets_focus(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        state = daemon.DaemonState(current_focused_address="0xddd")
        daemon.handle_active_window_changed_event(state, "aaa")
        offscreen_calls = [
            c for c in mock_subprocess_run.call_args_list if "movewindowpixel" in str(c)
        ]
        assert len(offscreen_calls) == 1
        assert "0xddd" in str(offscreen_calls[0])


class TestHandleCloseWindowEvent:
    def test_restores_previous_focus_when_current_is_closed(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        state = daemon.DaemonState(
            current_focused_address="0xabc",
            previous_focused_address="0xdef",
        )
        with patch("focus_daemon.time.sleep"):
            daemon.handle_close_window_event(state, "abc")
        assert state.current_focused_address == "0xdef"
        assert state.previous_focused_address == ""

    def test_clears_previous_when_previous_is_closed(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        state = daemon.DaemonState(
            current_focused_address="0xabc",
            previous_focused_address="0xdef",
        )
        daemon.handle_close_window_event(state, "def")
        assert state.previous_focused_address == ""
        assert state.current_focused_address == "0xabc"

    def test_delays_focus_dispatch_to_survive_layout_autofocus_race(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        state = daemon.DaemonState(
            current_focused_address="0xclipse",
            previous_focused_address="0xwezterm",
        )
        call_order = []
        with patch(
            "focus_daemon.time.sleep",
            side_effect=lambda _: call_order.append("sleep"),
        ):
            original_run = mock_subprocess_run.side_effect

            def tracking_side_effect(args, **kwargs):
                if "focuswindow" in str(args):
                    call_order.append("focuswindow")
                if original_run:
                    return original_run(args, **kwargs)
                from unittest.mock import MagicMock

                return MagicMock(stdout="", returncode=0)

            mock_subprocess_run.side_effect = tracking_side_effect
            daemon.handle_close_window_event(state, "clipse")

        assert call_order == ["sleep", "focuswindow"]


class TestMoveFloatingWindowsOffscreen:
    def test_moves_floating_windows_when_tiled_gets_focus(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        daemon.move_floating_windows_offscreen("0xaaa")
        offscreen_calls = [
            c for c in mock_subprocess_run.call_args_list if "movewindowpixel" in str(c)
        ]
        assert len(offscreen_calls) == 1
        assert "0xddd" in str(offscreen_calls[0])

    def test_never_moves_pinned_floating_windows_offscreen(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        daemon.move_floating_windows_offscreen("0xaaa")
        all_offscreen_args = " ".join(
            str(c)
            for c in mock_subprocess_run.call_args_list
            if "movewindowpixel" in str(c)
        )
        assert "0xeee" not in all_offscreen_args

    def test_skips_when_focused_is_floating(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        daemon.move_floating_windows_offscreen("0xddd")
        offscreen_calls = [
            c for c in mock_subprocess_run.call_args_list if "movewindowpixel" in str(c)
        ]
        assert len(offscreen_calls) == 0


class TestCollectFloatingWindowAddresses:
    def test_finds_floating_non_pinned_on_workspace(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        addresses = daemon.collect_floating_window_addresses_on_workspace(1, "0xaaa")
        assert addresses == ["0xddd"]

    def test_excludes_pinned_floating_windows(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        addresses = daemon.collect_floating_window_addresses_on_workspace(1, "0xaaa")
        assert "0xeee" not in addresses

    def test_excludes_specified_address(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        addresses = daemon.collect_floating_window_addresses_on_workspace(1, "0xddd")
        assert addresses == []


class TestEventHandlerDispatch:
    def test_all_required_events_have_handlers(self):
        required_events = {
            "activewindowv2",
            "closewindow",
        }
        assert required_events == set(daemon.EVENT_HANDLERS.keys())
