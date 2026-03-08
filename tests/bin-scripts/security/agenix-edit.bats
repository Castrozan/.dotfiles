#!/usr/bin/env bats

load '../../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "errors when no secret name provided" {
    assert_fails_with "Secret name required"
}

@test "uses agenix to edit secrets" {
    assert_script_source_matches "agenix.*-e"
}
