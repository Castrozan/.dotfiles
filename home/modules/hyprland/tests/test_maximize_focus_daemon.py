from unittest.mock import patch

import maximize_focus_daemon as daemon


class TestDaemonState:
    def test_initial_state_has_empty_workspace_tracking(self):
        state = daemon.DaemonState()
        assert state.maximized_workspace_ids == set()
        assert state.current_focused_address == ""
        assert state.previous_focused_address == ""


class TestInitializeMaximizedWorkspaceTracking:
    def test_tracks_workspaces_with_fullscreen_windows(
        self, hyprctl_response_builder, sample_hyprland_workspaces
    ):
        hyprctl_response_builder("workspaces", sample_hyprland_workspaces)
        state = daemon.DaemonState()
        daemon.initialize_maximized_workspace_tracking(state)
        assert state.maximized_workspace_ids == {1, 2}

    def test_clears_previous_tracking_on_reinitialize(
        self, hyprctl_response_builder, sample_hyprland_workspaces
    ):
        state = daemon.DaemonState(maximized_workspace_ids={5, 6, 7})
        hyprctl_response_builder("workspaces", sample_hyprland_workspaces)
        daemon.initialize_maximized_workspace_tracking(state)
        assert state.maximized_workspace_ids == {1, 2}


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


class TestHandleFullscreenEvent:
    def test_adds_workspace_to_maximized_tracking(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow", {"address": "0xabc", "workspace": {"id": 3}}
        )
        state = daemon.DaemonState()
        daemon.handle_fullscreen_event(state, "1")
        assert 3 in state.maximized_workspace_ids

    def test_ignores_unfullscreen_events(self, hyprctl_response_builder):
        state = daemon.DaemonState()
        daemon.handle_fullscreen_event(state, "0")
        assert len(state.maximized_workspace_ids) == 0


class TestHandleCloseWindowEvent:
    @patch("maximize_focus_daemon.time.sleep")
    def test_restores_previous_focus_when_current_is_closed(
        self, mock_sleep, hyprctl_response_builder, sample_hyprland_workspaces
    ):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xdef", "workspace": {"id": 1}, "fullscreen": 1},
        )
        hyprctl_response_builder("workspaces", sample_hyprland_workspaces)
        hyprctl_response_builder("clients", [])
        state = daemon.DaemonState(
            current_focused_address="0xabc",
            previous_focused_address="0xdef",
        )
        daemon.handle_close_window_event(state, "abc")
        assert state.current_focused_address == "0xdef"
        assert state.previous_focused_address == ""

    @patch("maximize_focus_daemon.time.sleep")
    def test_clears_previous_when_previous_is_closed(
        self, mock_sleep, hyprctl_response_builder, sample_hyprland_workspaces
    ):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xabc", "workspace": {"id": 1}, "fullscreen": 1},
        )
        hyprctl_response_builder("workspaces", sample_hyprland_workspaces)
        hyprctl_response_builder("clients", [])
        state = daemon.DaemonState(
            current_focused_address="0xabc",
            previous_focused_address="0xdef",
        )
        daemon.handle_close_window_event(state, "def")
        assert state.previous_focused_address == ""
        assert state.current_focused_address == "0xabc"


class TestHandleOpenWindowEvent:
    def test_maximizes_new_window_on_tracked_workspace(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        hyprctl_response_builder(
            "activewindow", {"address": "0xaaa", "workspace": {"id": 1}}
        )
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.handle_open_window_event(state, "aaa,kitty,Terminal")
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert len(batch_calls) > 0

    def test_ignores_window_on_untracked_workspace(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        state = daemon.DaemonState(maximized_workspace_ids={5})
        daemon.handle_open_window_event(state, "aaa,kitty,Terminal")

    def test_skips_floating_window_on_tracked_workspace(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        hyprctl_response_builder(
            "activewindow", {"address": "0xddd", "workspace": {"id": 1}}
        )
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.handle_open_window_event(state, "ddd,pavucontrol,Volume")
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl" and "--batch" in c[0][0]
        ]
        assert len(batch_calls) == 0


class TestHandleCloseWindowEventRegroupsRemainingWindows:
    @patch("maximize_focus_daemon.time.sleep")
    def test_ensures_remaining_windows_stay_grouped_after_close(
        self, mock_sleep, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 1}, "fullscreen": 1},
        )
        hyprctl_response_builder("workspaces", [{"id": 1, "hasfullscreen": True}])
        hyprctl_response_builder(
            "clients",
            [
                {
                    "address": "0xaaa",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": ["0xaaa", "0xccc"],
                },
                {
                    "address": "0xccc",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": ["0xaaa", "0xccc"],
                },
            ],
        )
        state = daemon.DaemonState(
            current_focused_address="0xbbb",
            previous_focused_address="0xaaa",
            maximized_workspace_ids={1},
        )

        with patch.object(
            daemon,
            "ensure_remaining_tiled_windows_on_active_workspace_are_grouped",
        ) as mock_ensure_grouped:
            daemon.handle_close_window_event(state, "bbb")
            mock_ensure_grouped.assert_called_once()


class TestForceRemaximizeActiveWorkspace:
    def test_forces_fullscreen_even_when_already_fullscreen(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 1}, "fullscreen": 1},
        )
        hyprctl_response_builder("clients", sample_hyprland_clients)
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.force_remaximize_active_workspace(state)
        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl"
            and "--batch" in c[0][0]
            and "fullscreen 1 unset" in str(c[0][0])
            and "fullscreen 1 set" in str(c[0][0])
        ]
        assert len(batch_calls) > 0

    def test_removes_tracking_when_no_tiled_windows(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 1}, "fullscreen": 1},
        )
        hyprctl_response_builder("clients", [])
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.force_remaximize_active_workspace(state)
        assert 1 not in state.maximized_workspace_ids

    def test_skips_untracked_workspace(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 5}, "fullscreen": 1},
        )
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.force_remaximize_active_workspace(state)


class TestHandleCloseWindowEventForceRemaximizes:
    @patch("maximize_focus_daemon.time.sleep")
    def test_close_event_uses_force_remaximize_not_conditional(
        self, mock_sleep, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 1}, "fullscreen": 1},
        )
        hyprctl_response_builder("workspaces", [{"id": 1, "hasfullscreen": True}])
        hyprctl_response_builder(
            "clients",
            [
                {
                    "address": "0xaaa",
                    "workspace": {"id": 1},
                    "floating": False,
                    "grouped": ["0xaaa"],
                },
            ],
        )
        state = daemon.DaemonState(
            current_focused_address="0xbbb",
            previous_focused_address="0xaaa",
            maximized_workspace_ids={1},
        )

        with patch.object(
            daemon,
            "ensure_remaining_tiled_windows_on_active_workspace_are_grouped",
        ):
            daemon.handle_close_window_event(state, "bbb")

        batch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if c[0][0][0] == "hyprctl"
            and "--batch" in c[0][0]
            and "fullscreen 1 unset" in str(c[0][0])
        ]
        assert len(batch_calls) > 0


class TestRemaximizeActiveWorkspaceIfNeeded:
    def test_remaximizes_when_tracked_and_not_fullscreen(
        self, mock_subprocess_run, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 1}, "fullscreen": 0},
        )
        hyprctl_response_builder("clients", sample_hyprland_clients)
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.remaximize_active_workspace_if_needed(state)
        dispatch_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if len(c[0][0]) > 1 and "fullscreen 1 set" in str(c[0][0])
        ]
        assert len(dispatch_calls) > 0

    def test_skips_when_already_fullscreen(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 1}, "fullscreen": 1},
        )
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.remaximize_active_workspace_if_needed(state)

    def test_removes_tracking_when_no_tiled_windows(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "activewindow",
            {"address": "0xaaa", "workspace": {"id": 1}, "fullscreen": 0},
        )
        hyprctl_response_builder("clients", [])
        state = daemon.DaemonState(maximized_workspace_ids={1})
        daemon.remaximize_active_workspace_if_needed(state)
        assert 1 not in state.maximized_workspace_ids


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
            "fullscreen",
            "closewindow",
            "openwindow",
            "workspace",
        }
        assert required_events == set(daemon.EVENT_HANDLERS.keys())
