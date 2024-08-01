#!/bin/bash

# Test if brew is installed
brew_test() {

    if ! brew --version; then
        print "brew is not installed." $RED
        exit 1
    else
        print "brew is installed." $GREEN
        exit 0
    fi
}

# Run the test
brew_test