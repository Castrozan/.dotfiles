#!/usr/bin/env bats
# Tests for on script (obsidian note creator)

setup() {
    SCRIPT="$BATS_TEST_DIRNAME/../../bin/on"
}

@test "on: errors when no filename provided" {
    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"file name must be set"* ]]
}
