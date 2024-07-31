#!/bin/bash

# Function to iterate over install scripts
iterate_install_scripts() {
    local dir=$INSTALL_SCRIPTS_DIR

    for file in "$dir"/*.sh; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            if ask "Do you want to install ${filename}?"; then
                . "$file" # source install script
            fi
        fi
    done
}
