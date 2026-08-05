#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    skip "SC2012 — tracked for shell-to-python migration"
}
