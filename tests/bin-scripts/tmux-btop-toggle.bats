#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "toggles btop pane in tmux" {
    assert_script_source_matches "btop"
}
