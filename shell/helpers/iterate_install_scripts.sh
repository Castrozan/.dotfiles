#!/bin/bash

# Function to iterate over install scripts
iterate_install_scripts() {
    echo $DOTFILES_HOME
    echo $INSTALL_SCRIPT_DIR
    echo "/pkgs/*"
    echo $(echo "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/pkgs/*")
    for file in $(echo "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/pkgs/*"); do
        filename=$(basename "$file")
        if ask "Do you want to install ${filename}?"; then
            if [ -f "$file" ]; then
                . "$file" # source install script
            fi
        fi
    done
}