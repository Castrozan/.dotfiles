#!/usr/bin/env bash

. "./shell/src/ask.sh"
. "./shell/src/print.sh"

# Function to install scripts
install_scripts() {
    local scripts=

    scripts=$(_get_scripts)

    for script in $scripts; do
        if ask "Do you want to install $script?"; then
            local file="$HOME/bin/$script"

            # Check if the file exists before making it executable
            if [ -f "$file" ]; then
                _make_file_executable "$file"
            else
                print "Error: File $file does not exist." "$_RED"
            fi
        fi
    done
}

# Function to get scripts to install
_get_scripts() {
    if [ -n "$_DOTFILES_SCRIPTS_TO_INSTALL" ]; then
        echo "$_DOTFILES_SCRIPTS_TO_INSTALL"
    elif [ -d "$HOME/bin/" ]; then
        ls -1 "$HOME/bin/"
    else
        print "Error: Directory $HOME/bin does not exist." "$_RED"
        return 1
    fi
}

# Function to make a file executable
# $1: file path
_make_file_executable() {
    local file="$1"

    if chmod +x "$file"; then
        print "Successfully made $file executable." "$_GREEN"
    else
        print "Error: Failed to make $file executable." "$_RED"
    fi
}
