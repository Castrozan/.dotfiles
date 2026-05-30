#!/usr/bin/env bats

load '../../../../../tests/helpers/bash-script-assertions'

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "rejects fewer than three arguments" {
	assert_fails_with "usage"
	assert_fails_with "usage" %1
	assert_fails_with "usage" %1 %2
}

@test "kills the dead pane and waits for the layout to settle before re-zooming" {
	assert_script_source_matches 'tmux kill-pane -t "\$dead_pane_id"'
	assert_pattern_appears_before 'tmux kill-pane' 'while tmux list-panes'
	assert_pattern_appears_before 'while tmux list-panes' 'tmux resize-pane -Z'
}

@test "re-zooms only when the previous pane was zoomed and is not already zoomed" {
	assert_script_source_matches 'previous_pane_was_zoomed" = "1"'
	assert_script_source_matches 'window_zoomed_flag.*= "0"'
}
