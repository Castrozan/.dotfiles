#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	export SCRIPT_UNDER_TEST="$DOTFILES_ROOT_DIRECTORY/machine-configuration/terminal/multiplexer/tmux/scripts/tmux-pane-toggle"
}

@test "rejects fewer than two arguments" {
	assert_fails_with "usage"
	assert_fails_with "usage" only-title
}
