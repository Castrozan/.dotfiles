#!/usr/bin/env bats

load '../../../../tests/helpers/bash-script-assertions'

@test "is nix template with substitution tokens" {
    assert_script_source_matches "@EXTRA_PATH@"
    assert_script_source_matches "@REAL_XWAYLAND@"
}

@test "uses strict error handling" {
    assert_uses_strict_error_handling
}

@test "has main entry point" {
    assert_script_source_matches 'main "\$@"'
}

@test "generates xauthority file" {
    assert_script_source_matches "xauth"
}

@test "propagates xauthority to user session" {
    assert_script_source_matches "dbus-update-activation-environment"
}
