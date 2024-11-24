#!/usr/bin/env bash

. "./shell/src/is_installed.sh"
. "./shell/src/install_pkg.sh"
. "./shell/src/is_already_installed.sh"

# Function to install a package
# $1: package name
# $2: custom package manager (optional)
should_install() {
    if is_installed $1 $2; then
        is_already_installed $1
    else
        install_pkg $1 $2
    fi
}
