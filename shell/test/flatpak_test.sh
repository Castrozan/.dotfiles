#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if flatpak is installed
flatpak_test() {

    if ! flatpak --version; then
        print "Flatpak is not installed." "$_RED"
        exit 1
    else
        print "Flatpak is installed." "$_GREEN"
    fi
}

# Run the test
flatpak_test
