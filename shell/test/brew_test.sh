#!/usr/bin/env bash

# Test if brew is installed
brew_test() {
    print "TODO: fix brew on ci" $_RED
    print "Skip Test brew" $_RED
    # if ! brew --version; then
    #     print "brew is not installed." $_RED
    #     exit 1
    # else
    #     print "brew is installed." $_GREEN
    # fi
}

# Run the test
brew_test
