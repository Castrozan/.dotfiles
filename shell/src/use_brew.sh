#!/usr/bin/env bash

. "./shell/src/print.sh"

# Function to use brew
use_brew() {

    # Ask if brew should be installed
    if ask "Do you want to install Homebrew?"; then
        # Check if brew is installed
        if brew --version; then
            print "Homebrew is already installed." "$_YELLOW"
        else
            # Install Homebrew from https://brew.sh
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

            # Install gcc
            brew postinstall gcc
            # Add brew to PATH
            eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

            # Check if brew is installed
            if brew --version; then
                print "Homebrew installed." "$_GREEN"
            else
                print "Homebrew installation failed." "$_RED"
            fi
        fi
    fi
}
