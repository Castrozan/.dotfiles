#!/usr/bin/env bash

. "./shell/src/print.sh"

# Function to install a package
# $1: package name
# $2: custom package manager (optional)
install_pkg() {
    local pkg_mgr="${2:-$_PKG_MGR}" # Use $2 if provided, else default to $_PKG_MGR
    local pkg_name="$1"

    # Attempt to install the package
    if ! $pkg_mgr install "$pkg_name"; then
        # Check if the error is related to permission issues
        error_message=$($pkg_mgr install "$pkg_name" 2>&1)
        if echo "$error_message" | grep -q "Permission denied\|are you root"; then
            print "It looks like you don't have sufficient permissions to install $pkg_name." "$RED"
            if ask "Would you like to try running the command with sudo?"; then
                sudo $pkg_mgr install "$pkg_name"
            else
                print "Skipping the installation of $pkg_name." "$YELLOW"
            fi
        else
            print "An error occurred while trying to install $pkg_name:" "$RED"
            print "$error_message" "$RED"
        fi
    else
        print "Successfully installed $pkg_name." "$GREEN"
    fi
}
