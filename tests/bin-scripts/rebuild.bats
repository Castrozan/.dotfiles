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

@test "detects NixOS vs non-NixOS" {
    assert_script_source_matches "_is_nixos"
}

@test "supports both nixos-rebuild and home-manager" {
    assert_script_source_matches_all "nixos-rebuild" "home-manager"
}

@test "uses flake with submodules" {
    assert_script_source_matches 'submodules=1'
}

@test "initializes git submodules" {
    assert_script_source_matches "submodule update --init"
}
