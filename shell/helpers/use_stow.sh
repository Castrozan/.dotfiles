#!/bin/bash

# Function to use stow
use_stow() {

    # Tell that Stow is required to create symlinks
    echo "${YELLOW}${BOLD}Stow is required to create symlinks.${RESET}"
    should_install stow

    # Tell that Stow with --adopt flag is used
    # Stow will use --adopt flag to adopt existing plain text files
    # This will replace your config file with its content
    # adopted files can be reverted with git --reset hard <file>
    echo "${YELLOW}${BOLD}Stow will use --adopt flag to adopt existing plain text files${RESET}"
    echo "${YELLOW}${BOLD}This will replace your /dotfiles/.file with its content${RESET}"
    echo "${YELLOW}${BOLD}Adopted files can be reverted with git reset HEAD .file${RESET}"
    echo "${YELLOW}${BOLD}Check https://www.gnu.org/software/stow/manual/html_node/Invoking-Stow.html for more info${RESET}"
    if ask "Do you want to run 'stow --adopt .' and create symlinks?"; then
        $STOW_CLAUSE
        echo "${GREEN}Dotfiles stowed.${RESET}"
    fi
}
