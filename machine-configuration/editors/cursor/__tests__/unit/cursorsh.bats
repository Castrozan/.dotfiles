#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	export SCRIPT_UNDER_TEST="$DOTFILES_ROOT_DIRECTORY/machine-configuration/editors/cursor/scripts/cursorsh"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}
