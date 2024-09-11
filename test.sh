#!/bin/sh

# Tell that the script is sourcing helper files
printf "Sourcing helper files...\n"
for file in shell/src/*; do
    if [ -f "$file" ]; then
        # Source file and check for errors exiting if any
        # shellcheck disable=SC1090
        . "$file" || {
            echo "Error sourcing $file"
            exit 1
        }
    fi
done

# Function to run tests
run_tests
