#!/bin/bash

# Test if brew is installed
brew_test() {
    print "TODO: fix brew on ci" $RED
    print "Skip Test brew" $RED
    # if ! brew --version; then
    #     print "brew is not installed." $RED
    #     exit 1
    # else
    #     print "brew is installed." $GREEN
    # fi
}

# Run the test
brew_test