#!/usr/bin/env bash

# Test if node is installed
nodejs_test() {

    if ! node --version; then
        print "NodeJS is not installed." "$RED"
        exit 1
    else
        print "NodeJS is installed." "$GREEN"
    fi
}

# Run the test
nodejs_test
