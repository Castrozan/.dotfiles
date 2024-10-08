#!/bin/sh

. "./config.sh"
. "shell/src/print.sh"
. "shell/src/is_sourced.sh"

# Function to source config by file path
# $1: config file path
_source_config_by_name() {
    file="$1"

    if [ -f "$file" ]; then
        full_path="\$HOME/$_DOTFILES_DIR/$file"
        if is_sourced "$full_path"; then
            print "$full_path is already sourced in $_SH." "${YELLOW}"
        else
            # Add the source command to .bashrc
            # shellcheck disable=SC2028
            echo ". $full_path" >>"$_SH"
            print "$full_path has been sourced." "${GREEN}"
        fi
    else
        print "Config $file does not exist." "${RED}"
    fi
}

# Function to config scripts defined on _DOTFILES_CONFIGS_TO_INSTALL
# defined on the ./config.sh file
_declarative_config() {
    _configs=$_DOTFILES_CONFIGS_TO_INSTALL

    for _config in $_configs; do
        file="shell/configs/$_config.sh"

        _source_config_by_name "$file"
    done
}

# Function to config all configs that are in the /shell/configs directory
_interactive_config() {
    _dir=$_CONFIG_SCRIPTS_DIR

    for file in "$_dir"/*; do
        _source_config_by_name "$file"
    done
}

# Function to iterate and set config scripts
iterate_config_scripts() {

    # Check if configs are set to be installed declaratively
    if [ -n "$_DOTFILES_CONFIGS_TO_INSTALL" ]; then
        _declarative_config
    else
        _interactive_config
    fi
}
