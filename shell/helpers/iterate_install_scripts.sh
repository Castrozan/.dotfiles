#!/bin/bash

# Function to iterate over install scripts
iterate_install_scripts() {
    for file in "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/pkgs/*"; do
        if ask "Do you want to install $file?"; then
            if [ -f "$file" ]; then
                . "$file" # source install script
            fi
        fi
    done
}