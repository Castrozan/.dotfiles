#!/bin/bash

# Tell that the script is sourcing helper files
echo "Sourcing helper files...\n"
for file in shell/helpers/*; do
    if [ -f "$file" ]; then
        # Source file and check for errors exiting if any
        . "$file" || { echo "Error sourcing $file"; exit 1; }
    fi
done

# Function to run tests
run_tests
