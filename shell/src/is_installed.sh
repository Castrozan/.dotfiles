#!/usr/bin/env bash

# Function to check if a package is installed
# $1: package name
# $2: custom package manager (optional)
is_installed() {
    local pkg_mgr=$_PKG_MGR

    if [ -n "$2" ]; then
        pkg_mgr=$2
    fi

    case $pkg_mgr in
    apt)
        dpkg -l | grep -q "^ii\s\+$1\s"
        ;;
    brew)
        brew list | grep -q "^$1\$"
        ;;
    *)
        echo "Unsupported package manager: ${pkg_mgr}"
        ;;
    esac
}
