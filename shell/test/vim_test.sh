#!/usr/bin/env bash

# Test if vim is installed
vim_test() {

    if ! vim --version | head -n 1; then
        print "Vim is not installed." $RED
        exit 1
    else
        print "Vim is installed." $GREEN
    fi
}

# Run the test
vim_test
