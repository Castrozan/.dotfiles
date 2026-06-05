#!/usr/bin/env bats

load '../../../../../tests/helpers/bash-script-assertions'

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "rejects fewer than two arguments" {
	assert_fails_with "usage"
	assert_fails_with "usage" only-title
}

@test "splits, titles, and sends the command via send-keys" {
	assert_script_source_matches "tmux split-window"
	assert_script_source_matches 'tmux select-pane -t "\$new_pane_id" -T "\$pane_title"'
	assert_script_source_matches 'send-keys -t "\$new_pane_id"'
}

@test "detects the previous zoom state via window_zoomed_flag not the nonexistent pane_zoomed" {
	assert_script_source_matches "window_zoomed_flag"
	assert_script_source_does_not_match "pane_zoomed"
}

@test "toggles by selecting an existing pane with the same title" {
	assert_script_source_matches 'tmux list-panes'
	assert_script_source_matches 'tmux select-pane -t "\$existing_pane_id"'
	assert_script_source_matches 'resize-pane -Z -t "\$existing_pane_id"'
}

@test "delegates restoration to a server-side run-shell so the dying pane never owns the re-zoom" {
	assert_script_source_matches 'tmux run-shell -b'
	assert_script_source_matches 'tmux-restore-pane-after-toggle \$new_pane_id \$previous_pane_id \$previous_pane_was_zoomed'
}

@test "does not chain pane restoration after kill-pane in the dying shell" {
	assert_script_source_does_not_match 'kill-pane -t \$new_pane_id 2>/dev/null &&'
}
