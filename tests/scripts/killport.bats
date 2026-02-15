#!/usr/bin/env bats

load '../helpers/script'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "shows usage when no port provided" {
    assert_fails_with "Usage:"
}

@test "reports when no process found on unused port" {
    assert_fails_with "No process found" 59999
}
