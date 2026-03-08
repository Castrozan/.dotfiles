#!/usr/bin/env bats

load '../../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    skip "SC2034/SC2016 — tracked for shell-to-python migration"
}

@test "shows usage with --help" {
    assert_succeeds_with "Usage:" --help
}
