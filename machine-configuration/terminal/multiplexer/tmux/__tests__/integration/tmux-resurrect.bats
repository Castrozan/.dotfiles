#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	export SCRIPT_UNDER_TEST="$DOTFILES_ROOT_DIRECTORY/machine-configuration/terminal/multiplexer/tmux/scripts/tmux-resurrect"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	skip "SC2012 — tracked for shell-to-python migration"
}
