#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

@test "errors when no secret name provided" {
    assert_fails_with "Secret name required"
}
