#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/should_install.sh"
. "./shell/src/ask.sh"

# Function to use stow
use_stow() {

    # Tell that Stow is required to create symlinks
    print "Stow is required to create symlinks." "$YELLOW" "$BOLD"
    should_install stow

    # Tell that Stow with --adopt flag is used
    # Stow will use --adopt flag to adopt existing plain text files
    # This will replace your config file with its content
    # adopted files can be reverted with git --reset hard <file>
    print "Stow will use --adopt flag to adopt existing plain text files" "$YELLOW" "$BOLD"
    print "This will replace your /dotfiles/.file with its content" "$YELLOW" "$BOLD"
    print "Adopted files can be reverted with git reset HEAD .file" "$YELLOW" "$BOLD"
    print "Check https://www.gnu.org/software/stow/manual/html_node/Invoking-Stow.html for more info" "$YELLOW" "$BOLD"
    if ask "Do you want to run '$_STOW_CLAUSE' and create symlinks?"; then
        $_STOW_CLAUSE
        print "Dotfiles stowed." "$GREEN" "$BOLD"
    fi
}
