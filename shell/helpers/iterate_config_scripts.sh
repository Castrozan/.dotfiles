#!/bin/bash

# Function to iterate over config scripts
iterate_config_scripts() {
    local dir=$CONFIG_SCRIPTS_DIR

    for file in $dir*; do
        if [ -f "$file" ]; then
            local full_path="$DOTFILES_HOME/$file"
            if is_sourced "$full_path"; then
                echo "${YELLOW}$full_path is already sourced in $SH.${RESET}"
            else
                # Add the source command to .bashrc
                echo "# Files sourced by dotfiles at $DOTFILES_HOME" >> "$SH"
                echo ". $full_path" >> "$SH"
                echo "${GREEN}$full_path has been sourced.${RESET}"
            fi
        fi
    done
}