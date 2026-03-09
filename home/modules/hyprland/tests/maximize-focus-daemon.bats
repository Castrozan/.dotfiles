#!/usr/bin/env bats

load '../../../../tests/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict error handling" {
    assert_uses_strict_error_handling
}

@test "follows canonical script pattern with main entry point" {
    assert_script_source_matches '^main\(\)'
    assert_script_source_matches '^main$'
}

@test "uses readonly constants for configuration" {
    assert_script_source_matches_all \
        "readonly HYPRLAND_EVENT_SOCKET" \
        "readonly RECONNECT_INITIAL_DELAY_SECONDS" \
        "readonly RECONNECT_MAX_DELAY_SECONDS" \
        "readonly OPENED_WINDOW_WORKSPACE_LOOKUP_ATTEMPTS" \
        "readonly OPENED_WINDOW_WORKSPACE_LOOKUP_DELAY_SECONDS"
}

@test "private helpers prefixed with underscore" {
    assert_script_source_matches_all \
        "_get_active_window_fullscreen_state" \
        "_get_workspace_has_fullscreen_window" \
        "_get_active_workspace_id" \
        "_get_window_workspace_id_by_address" \
        "_get_opened_window_workspace_id" \
        "_is_workspace_tracked_as_maximized" \
        "_add_workspace_to_maximized_tracking" \
        "_remove_workspace_from_maximized_tracking" \
        "_handle_active_window_changed_event" \
        "_handle_fullscreen_event" \
        "_handle_close_window_event" \
        "_handle_open_window_event" \
        "_handle_hyprland_event" \
        "_initialize_maximized_workspace_tracking" \
        "_initialize_focused_window_tracking" \
        "_read_and_dispatch_hyprland_events" \
        "_wait_for_hyprland_socket" \
        "_connect_and_process_events_with_reconnect" \
        "_get_focused_window_properties" \
        "_get_floating_window_addresses_on_workspace" \
        "_move_floating_windows_offscreen" \
        "_restore_floating_window_to_center"
}

@test "handles all required hyprland events" {
    assert_script_source_matches_all \
        "activewindowv2)" \
        "fullscreen)" \
        "closewindow)" \
        "openwindow)"
}

@test "connects to hyprland event socket via netcat" {
    assert_script_source_matches 'nc -U "\$HYPRLAND_EVENT_SOCKET"'
}

@test "implements exponential backoff for reconnection" {
    assert_script_source_matches "reconnect_delay_seconds=.*reconnect_delay_seconds \* 2"
    assert_script_source_matches "RECONNECT_MAX_DELAY_SECONDS"
}

@test "tracks focus history for close-window restoration" {
    assert_script_source_matches "previous_focused_address"
    assert_script_source_matches "current_focused_address"
    assert_script_source_matches 'focuswindow "address:\$previous_focused_address"'
}

@test "re-maximizes windows after close on tracked workspaces" {
    assert_script_source_matches "fullscreen 1 set"
    assert_script_source_matches "_is_workspace_tracked_as_maximized"
}

@test "auto-maximizes newly opened windows on tracked workspaces" {
    assert_script_source_matches '_handle_open_window_event'
    assert_script_source_matches 'dispatch focuswindow.*dispatch fullscreen 1 set'
}

@test "moves floating windows offscreen when tiled window gets focus" {
    assert_script_source_matches "_move_floating_windows_offscreen"
    assert_script_source_matches 'movewindowpixel.*OFFSCREEN_POSITION'
}

@test "offscreen function filters by floating and non-pinned status" {
    assert_script_source_matches '.floating == true'
    assert_script_source_matches '.pinned == false'
}

@test "offscreen function scopes to same workspace" {
    assert_script_source_matches 'workspace.id == .*ws.*tonumber'
}

@test "offscreen function skips when focused window is floating" {
    assert_script_source_matches 'is_floating.*==.*true.*&& return'
}

@test "restores floating window to center when it gets focus" {
    assert_script_source_matches "_restore_floating_window_to_center"
    assert_script_source_matches "centerwindow"
}

@test "active window handler restores before hiding" {
    local script_path
    script_path="$(_resolve_script_under_test)"
    local handler_body
    handler_body=$(sed -n '/_handle_active_window_changed_event()/,/^}/p' "$script_path")
    local restore_line offscreen_line
    restore_line=$(echo "$handler_body" | grep -n "_restore_floating_window_to_center" | head -1 | cut -d: -f1)
    offscreen_line=$(echo "$handler_body" | grep -n "_move_floating_windows_offscreen" | head -1 | cut -d: -f1)
    [ -n "$restore_line" ] && [ -n "$offscreen_line" ] && [ "$restore_line" -lt "$offscreen_line" ]
}

@test "uses readonly offscreen position constant" {
    assert_script_source_matches "readonly OFFSCREEN_POSITION"
}

@test "floating windows stay on same workspace for alt-tab visibility" {
    run grep -c "movetoworkspacesilent" "$(_resolve_script_under_test)"
    [ "$output" -eq 0 ] || {
        run grep "movetoworkspacesilent.*special:minimized" "$(_resolve_script_under_test)"
        [ "$status" -ne 0 ]
    }
}
