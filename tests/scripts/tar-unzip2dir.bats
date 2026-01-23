#!/usr/bin/env bats
# Tests for tar-unzip2dir script

setup() {
    SCRIPT="$BATS_TEST_DIRNAME/../../bin/tar-unzip2dir"
    TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR"

    # Create test archive
    mkdir -p source
    echo "test content" > source/file.txt
    tar -czf test.tar.gz source
    rm -rf source
}

teardown() {
    rm -rf "$TEST_DIR"
}

@test "tar-unzip2dir: shows usage when no file provided" {
    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "tar-unzip2dir: errors on non-existent file" {
    run "$SCRIPT" nonexistent.tar.gz
    [ "$status" -eq 1 ]
    [[ "$output" == *"not found"* ]]
}

@test "tar-unzip2dir: errors on wrong file type" {
    touch wrongtype.zip
    run "$SCRIPT" wrongtype.zip
    [ "$status" -eq 1 ]
    [[ "$output" == *".tar.gz or .tgz"* ]]
}

@test "tar-unzip2dir: extracts to named directory" {
    run "$SCRIPT" test.tar.gz
    [ "$status" -eq 0 ]
    [ -d "test" ]
    [ -f "test/source/file.txt" ]
    [[ "$output" == *"Success"* ]]
}

@test "tar-unzip2dir: errors if output directory exists" {
    mkdir test
    run "$SCRIPT" test.tar.gz
    [ "$status" -eq 1 ]
    [[ "$output" == *"already exists"* ]]
}
