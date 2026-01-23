#!/usr/bin/env bats
# Tests for killport script

setup() {
    SCRIPT="$BATS_TEST_DIRNAME/../../bin/killport"
}

@test "killport: shows usage when no port provided" {
    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "killport: reports when no process found on unused port" {
    run "$SCRIPT" 59999
    [ "$status" -eq 1 ]
    [[ "$output" == *"No process found"* ]]
}
