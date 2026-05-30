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
	assert_script_source_matches 'tmux send-keys -t "\$new_pane_id"'
}

@test "toggles by selecting an existing pane with the same title" {
	assert_script_source_matches 'tmux list-panes'
	assert_script_source_matches 'tmux select-pane -t "\$existing_pane_id"'
	assert_script_source_matches 'tmux resize-pane -Z'
}

@test "restores the previous pane via server-side run-shell so the dying pane never owns the re-zoom" {
	assert_script_source_matches 'tmux run-shell -b'
	assert_script_source_matches 'tmux resize-pane -Z -t \$previous_pane_id'
}

@test "does not chain pane restoration after kill-pane in the dying shell" {
	assert_script_source_does_not_match 'kill-pane -t \$new_pane_id 2>/dev/null &&'
}
