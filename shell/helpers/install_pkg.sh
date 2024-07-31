#!/bin/bash

# Function to install a package
# $1: package name
install_pkg() {
    cd $DEFAULT_INSTALL_DIR

    $INSTALL_CLAUSE $1
    echo "Installing $1..."

    cd $DOTFILES_HOME
}