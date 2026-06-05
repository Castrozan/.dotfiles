#!/usr/bin/env bats

load '../../../../../tests/helpers/bash-script-assertions'

setup() {
	export SCRIPT_UNDER_TEST="$DOTFILES_ROOT_DIRECTORY/.config/tmux/binds.conf"
}

@test "every toggle binding backgrounds its dispatch with run-shell -b" {
	for key in i b e v t; do
		assert_script_source_matches "^bind $key run-shell -b "
	done
}

@test "every toggle binding feeds pane context so the script makes no display-message round-trip" {
	for key in i b e v t; do
		assert_script_source_matches "^bind $key .*'#\{pane_current_path\}' '#\{window_id\}' '#\{pane_id\}' '#\{window_zoomed_flag\}'"
	done
}

@test "no toggle binding falls back to a blocking foreground run-shell" {
	assert_script_source_does_not_match "^bind [ibevt] run-shell \""
}
