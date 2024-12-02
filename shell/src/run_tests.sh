#!/usr/bin/env bash

. "./shell/src/print.sh"

# Function to run tests
run_tests() {
    local dir=$_TEST_DIR

    print "Running test ..." "$_YELLOW"
    for file in $dir/*; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            print "\n${filename}" "$_YELLOW"
            . "$file" # source test script
        fi
    done
}
