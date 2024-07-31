#!/bin/bash

# Function to iterate over install scripts
iterate_install_scripts() {
    local dir=$INSTALL_SCRIPTS_DIR

    echo "dir: $dir"

    # Check if the directory exists
    if [ ! -d "$dir" ]; then
        echo "Directory does not exist: $dir"
        return 1
    fi

    # Use a fallback method to handle file expansion
    files=$(ls "$dir"/*.sh 2>/dev/null)

    # Check if files variable is empty
    if [ -z "$files" ]; then
        echo "No .sh files found in $dir"
        return 1
    fi

    for file in $files; do
        echo "file: $file"

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
