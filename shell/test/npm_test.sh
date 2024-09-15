#!/bin/bash

# Test if npm is installed
npm_test() {

    if ! npm --version; then
        print "Npm is not installed." "$RED"
        exit 1
    else
        print "Npm is installed." "$GREEN"
    fi
}

# Run the test
npm_test
