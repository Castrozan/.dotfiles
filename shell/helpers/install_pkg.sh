#!/bin/bash

# Function to install a package
# $1: package name
# $2: custom package manager (optional)
install_pkg() {
    local pkg_mgr=$PKG_MGR_INSTALL

    if [ -n "$2" ]; then
        pkg_mgr=$2
    fi

    $pkg_mgr install $1
    echo "Installing $1..."
}
