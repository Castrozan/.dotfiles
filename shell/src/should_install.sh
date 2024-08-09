#!/bin/bash

# Function to install a package
# $1: package name
# $2: custom package manager (optional)
should_install() {
    if is_installed $1 $2; then
        echo "${YELLOW}$1 is already installed.${RESET}"
    else
        install_pkg $1 $2
    fi
}