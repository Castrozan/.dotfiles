#!/bin/bash

# Function to run tests
run_tests() {
    local dir=$TEST_DIR

    print "Running test ..." $YELLOW
    for file in $dir*; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            . "$file" # source install script
            echo ""
        fi
    done
}
