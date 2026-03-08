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

@test "configures logind to ignore lid switch" {
    assert_script_source_matches "HandleLidSwitch=ignore"
}

@test "restarts systemd-logind" {
    assert_script_source_matches "systemctl restart systemd-logind"
}
