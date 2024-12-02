#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if stow is installed
stow_test() {

    if ! stow --version; then
        print "Stow is not installed." "$_RED"
        exit 1
    else
        print "Stow is installed." "$_GREEN"
    fi
}

# Run the test
stow_test
