#!/usr/bin/env bash

# Test if stow is installed
stow_test() {

    if ! stow --version; then
        print "Stow is not installed." $RED
        exit 1
    else
        print "Stow is installed." $GREEN
    fi
}

# Run the test
stow_test
