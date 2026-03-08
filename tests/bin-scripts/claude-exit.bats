#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "validates process name before killing" {
    assert_script_source_matches 'Safety check'
}

@test "uses SIGTERM for clean shutdown" {
    assert_script_source_matches "SIGTERM"
}
