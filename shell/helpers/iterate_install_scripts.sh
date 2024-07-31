#!/bin/bash

# Function to iterate over install scripts
# $1: directory with install scripts
iterate_install_scripts() {
    for file in "$1"; do
        filename=$(basename "$file")
        if ask "Do you want to install ${filename}?"; then
            if [ -f "$file" ]; then
                . "$file" # source install script
            fi
        fi
    done
}