#!/bin/bash

# Function to iterate over config scripts
iterate_config_scripts() {
    local dir=$_CONFIG_SCRIPTS_DIR

    for file in $dir*; do
        if [ -f "$file" ]; then
            local full_path="$_DOTFILES_HOME/$file"
            if is_sourced "$full_path"; then
                echo "${YELLOW}$full_path is already sourced in $_SH.${RESET}"
            else
                # Add the source command to .bashrc
                echo "\n. $full_path" >>"$_SH"
                echo "${GREEN}$full_path has been sourced.${RESET}"
            fi
        fi
    done
}
