#!/bin/bash

# Function to install a package
# $1: package name
install_pkg() {
    $INSTALL_CLAUSE $1
    echo "Installing $1..."
}