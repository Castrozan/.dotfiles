#!/bin/bash

# Function to use brew
use_brew() {

    # Ask if brew should be installed
    if ask "Do you want to install Homebrew?"; then
        # Check if brew is installed
        if brew --version; then
            echo "${YELLOW}Homebrew is already installed.${RESET}"
        else
            # Install Homebrew from https://brew.sh
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

            # Add Homebrew to PATH
            (echo; echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"') >> $SH
            eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

            # Check if brew is installed
            if brew --version; then
                echo "${GREEN}Homebrew installed.${RESET}"
            else 
                echo "${RED}Homebrew installation failed.${RESET}"
            fi
        fi
    fi
}
