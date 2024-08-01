#!/bin/bash

# Function to iterate over config scripts
iterate_config_scripts() {
    local dir=$CONFIG_SCRIPTS_DIR

    for file in $dir*; do
        if [ -f "$file" ]; then
            if is_sourced "$file"; then
                echo "${YELLOW}$file is already sourced in $SH.${RESET}"
            else
                # Add the source command to .bashrc
                echo "# Files sourced by dotfiles at $DOTFILES_HOME" >> "$SH"
                echo ". $file" >> "$SH"
                echo "${GREEN}$file has been sourced.${RESET}"
            fi
        fi
    done
}