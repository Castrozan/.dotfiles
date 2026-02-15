#!/usr/bin/env bats

load '../helpers/script'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "errors when no filename provided" {
    assert_fails_with "file name must be set"
}
