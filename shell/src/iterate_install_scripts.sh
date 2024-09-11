#!/bin/sh

. "shell/src/ask.sh"

# Function to iterate over install scripts
iterate_install_scripts() {
    _dir=$_INSTALL_SCRIPTS_DIR

    for file in "$_dir"/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            if ask "Do you want to install ${filename}?"; then
                # shellcheck disable=SC1090
                . "$file" # source install script
            fi
        fi
    done
}
