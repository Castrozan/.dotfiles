#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/is_desktop_environment.sh"
. "./shell/src/is_installed.sh"
. "./shell/src/is_ubuntu.sh"
. "./shell/src/has_snap.sh"

# Install Postman
install_postman() {
    if ! has_snap; then
        print "Snap is not available. Please install snap first." "$_RED"
        exit 1
    fi

    if ! is_ubuntu; then
        print "This installation method is only supported on Ubuntu." "$_RED"
        exit 1
    fi

    print "Installing Postman..." "$_YELLOW"
    sudo snap install postman
}

if is_desktop_environment; then
    # Check if Postman is installed
    if is_installed "postman" "snap" >/dev/null 2>&1; then
        print "Postman already installed" "$_YELLOW"
    else
        install_postman
    fi
fi 