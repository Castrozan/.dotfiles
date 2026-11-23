#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

@test "shows usage when no port provided" {
    assert_fails_with "Usage:"
}

@test "reports when no process found on unused port" {
    assert_fails_with "No process found" 59999
}
