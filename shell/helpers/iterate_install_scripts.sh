#!/bin/bash

# Function to iterate over install scripts
# $1: directory with install scripts
iterate_install_scripts() {
    for file in $1; do
        if [ -f "$file" ]; then
            . "$file" # source install script
        fi
    done
}