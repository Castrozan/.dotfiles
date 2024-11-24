#!/usr/bin/env bash

# Test if flatpak is installed
flatpak_test() {

    if ! flatpak --version; then
        print "Flatpak is not installed." "$RED"
        exit 1
    else
        print "Flatpak is installed." "$GREEN"
    fi
}

# Run the test
flatpak_test
