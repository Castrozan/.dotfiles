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

@test "shows usage when no subcommand provided" {
    assert_fails_with "Usage:"
}

@test "supports get set info subcommands" {
    assert_script_source_matches_all "get)" "set)" "info)"
}
