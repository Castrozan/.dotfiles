#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "refuses when no terminal is attached" {
	assert_fails_with "no terminal is attached" "/repository/.git/COMMIT_EDITMSG"
}

@test "names the non-interactive alternatives it refuses in favour of" {
	assert_fails_with "git commit -m" "/repository/.git/COMMIT_EDITMSG"
}

@test "opens neovim once a terminal is attached" {
	assert_script_source_matches 'exec nvim "\$@"'
}
