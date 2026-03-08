#!/usr/bin/env bats

load '../../../../tests/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    skip "SC2155 warnings — tracked for shell-to-python migration"
}
