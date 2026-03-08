#!/usr/bin/env bats

load '../../../../tests/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "commits private-config submodule before main repo" {
    assert_pattern_appears_before 'git -C "$SUB"' 'git -C "$DOTFILES"'
}
