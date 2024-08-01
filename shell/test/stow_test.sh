#!/bin/bash

# Test if stow is installed
stow_test() {

    if ! stow --version; then
        print "Stow is not installed." $RED
        return 1
    else
        print "Stow is installed." $GREEN
        return 0
    fi
}

# Run the test
stow_test