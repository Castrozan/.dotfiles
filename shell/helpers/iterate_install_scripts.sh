#!/bin/bash

# Function to iterate over install scripts
iterate_install_scripts() {
    local dir=$INSTALL_SCRIPTS_DIR

    echo "dir: $dir"
    for file in "$dir"/*.sh; do
        echo file: $file

        if [ -f "$file" ]; then
            echo "file is a file"
            local filename=$(basename "$file")
            if ask "Do you want to install ${filename}?"; then
                echo source install script
                . "$file" # source install script
            fi
        fi
    done
}
