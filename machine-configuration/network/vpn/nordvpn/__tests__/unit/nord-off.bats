#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}
