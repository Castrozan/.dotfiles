#!/usr/bin/env bash

# Function to check if a package is installed
# $1: package name
# $2: custom package manager (optional)
is_installed() {
    local pkg_mgr=$_PKG_MGR

    if [ -n "$2" ]; then
        pkg_mgr=$2
    fi

    # TODO: make package manager detection more robust
    #   like sourcing them from a bash array
    #   from another file
    case $pkg_mgr in
    apt)
        dpkg -l | grep -q "^ii\s\+$1\s"
        ;;
    brew)
        brew list | grep -q "^$1\$"
        ;;
    snap)
        snap list | grep -q "$1"
        ;;
    nix)
        nix-env -q | grep -q "$1"
        ;;
    appimage)
        [ -f "$HOME/.local/bin/$1" ] || \
        [ -f "$HOME/.local/share/$1/$1.AppImage" ]
        ;;
    *)
        echo "Unsupported package manager: ${pkg_mgr}"
        ;;
    esac
}
