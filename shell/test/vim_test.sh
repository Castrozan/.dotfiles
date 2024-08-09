#!/bin/bash

# Test if vim is installed
vim_test() {

    if ! vim --version; then
        print "Vim is not installed." $RED
        exit 1
    else
        print "Vim is installed." $GREEN
        exit 0
    fi
}

# Run the test
vim_test