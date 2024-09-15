#!/bin/sh

. "shell/src/print.sh"
. "shell/src/is_sourced.sh"

# Function to iterate over config scripts
iterate_config_scripts() {
    _dir=$_CONFIG_SCRIPTS_DIR

    for file in "$_dir"/*; do
        if [ -f "$file" ]; then
            full_path="$_DOTFILES_HOME/$file"
            if is_sourced "$full_path"; then
                print "$full_path is already sourced in $_SH." "${YELLOW}"
            else
                # Add the source command to .bashrc
                # shellcheck disable=SC2028
                echo "\n. $full_path" >>"$_SH"
                print "$full_path has been sourced." "${GREEN}"
            fi
        fi
    done
}
