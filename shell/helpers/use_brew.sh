#!/bin/bash

# Function to use brew
use_brew() {

    # Ask if brew should be installed
    if ask "Do you want to install Homebrew?"; then
        # Check if brew is installed
        if command -v brew &> /dev/null; then
            echo "${YELLOW}Homebrew is already installed.${RESET}"
        else
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            echo "${GREEN}Homebrew installed.${RESET}"
        fi
    fi
}
