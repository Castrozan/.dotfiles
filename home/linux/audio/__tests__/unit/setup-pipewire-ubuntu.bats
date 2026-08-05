#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "installs pipewire packages" {
    assert_script_source_matches "pipewire-pulse"
}
