#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	export SCRIPT_UNDER_TEST="$DOTFILES_ROOT_DIRECTORY/machine-configuration/terminal/multiplexer/tmux/scripts/tmux-restore-pane-after-toggle"
}

@test "rejects fewer than three arguments" {
	assert_fails_with "usage"
	assert_fails_with "usage" %1
	assert_fails_with "usage" %1 %2
}
