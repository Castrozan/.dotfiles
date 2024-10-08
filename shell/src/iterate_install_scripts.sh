#!/bin/sh

. "./config.sh"
. "shell/src/ask.sh"

_declarative_install() {
    _pkgs=$_DOTFILES_PACKAGES_TO_INSTALL

    for _pkg in $_pkgs; do
        file="shell/pkgs/$_pkg.sh"

        if [ -f "$file" ]; then
            if ask "Do you want to install $_pkg?"; then
                # shellcheck disable=SC1090
                . "$file" # source install script
            fi
        fi
    done
}

_interactive_install() {
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

# Function to install pkgs
# and source the install scripts
iterate_install_scripts() {

    # Check if pkgs are set to install declaratively
    if [ -n "$_DOTFILES_PACKAGES_TO_INSTALL" ]; then
        _declarative_install
    else
        _interactive_install
    fi
}
