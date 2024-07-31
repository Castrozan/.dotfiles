#!/bin/bash

# Wrapper function to install a package
# $1: package name
should_install() {
    if ask "Do you want to install $1?"; then
        if is_installed $1; then
            echo "${YELLOW}$1 is already installed.${RESET}"
        else
            install_pkg $1
        fi
    fi
}