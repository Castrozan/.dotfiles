#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

setup() {
    TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR" || return 1

    mkdir -p source
    echo "test content" > source/file.txt
    tar -czf test.tar.gz source
    rm -rf source
}

teardown() {
    rm -rf "$TEST_DIR"
}

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict mode" {
    assert_strict_mode
}

@test "shows usage when no file provided" {
    assert_fails_with "Usage:"
}

@test "errors on non-existent file" {
    assert_fails_with "not found" nonexistent.tar.gz
}

@test "errors on wrong file type" {
    touch wrongtype.zip
    assert_fails_with ".tar.gz or .tgz" wrongtype.zip
}

@test "extracts to named directory" {
    assert_succeeds_with "Success" test.tar.gz
    [ -d "test" ]
    [ -f "test/source/file.txt" ]
}

@test "errors if output directory exists" {
    mkdir test
    assert_fails_with "already exists" test.tar.gz
}
