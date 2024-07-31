#!/bin/bash

# Function to iterate over config scripts
# $1: directory with config scripts
iterate_config_scripts() {
    for file in $1; do
            if is_sourced "$file"; then
                echo "${YELLOW}$file is already sourced in $SH.${RESET}"
            else
                # Add the source command to .bashrc
                echo "# Files sourcered by dotfiles at $DOTFILES_HOME" >> "$SH"
                echo ". $file" >> "$SH"
                echo "${GREEN}$file has been sourced.${RESET}"
            fi
    done
}