#!/usr/bin/env bats

load '../../helpers/bash-script-assertions'

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

@test "shows usage when no arguments provided" {
    assert_fails_with "Usage:"
}

@test "supports volume brightness mute mic commands" {
    assert_script_source_matches_all "volume)" "brightness)" "mute)" "mic)"
}
