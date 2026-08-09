#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict error handling" {
    assert_uses_strict_error_handling
}

@test "installs the tailnet range into the main routing table" {
    assert_script_source_matches_all "100\.64\.0\.0/10" "table main"
}

@test "waits for the tailscale interface before routing" {
    assert_pattern_appears_before "ip link show" "ip route replace"
}
