#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

@test "errors when no filename provided" {
    assert_fails_with "file name must be set"
}
