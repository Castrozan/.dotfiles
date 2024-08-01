#!/bin/bash

# Tell that the script is sourcing helper files
echo "Sourcing helper files...\n"
for file in shell/helpers/*; do
    if [ -f "$file" ]; then
        . "$file" # Source the file
    fi
done

# Function to run tests
run_tests
