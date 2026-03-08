#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict error handling" {
    assert_uses_strict_error_handling
}

@test "has main entry point" {
    assert_script_source_matches 'main "\$@"'
}

@test "shows usage with --help" {
    assert_succeeds_with "Usage:" --help
}

@test "supports dry-run mode" {
    assert_script_source_matches "dry.run"
}

@test "has configurable generation count" {
    assert_script_source_matches "DEFAULT_GENERATIONS_TO_KEEP"
}
