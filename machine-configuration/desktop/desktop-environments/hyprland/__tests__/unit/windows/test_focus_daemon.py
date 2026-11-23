import focus_daemon as daemon


class TestDaemonState:
    def test_initial_state_has_empty_focus_tracking(self):
        state = daemon.DaemonState()
        assert state.current_focused_address == ""


class TestInitializeFocusedWindowTracking:
    def test_sets_current_focused_from_active_window(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow", {"address": "0xabc", "workspace": {"id": 1}}
        )
        state = daemon.DaemonState()
        daemon.initialize_focused_window_tracking(state)
        assert state.current_focused_address == "0xabc"


class TestHandleActiveWindowChangedPinnedWindowSurvival:
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


class TestCollectFloatingWindowAddresses:
    def test_excludes_specified_address(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        addresses = daemon.collect_floating_window_addresses_on_workspace(1, "0xddd")
        assert addresses == []


class TestEventHandlerDispatch:
    def test_only_handles_activewindowv2(self):
        assert set(daemon.EVENT_HANDLERS.keys()) == {"activewindowv2"}
