#!/bin/bash

# Test if zoxide is installed
zoxide_test() {

    if ! zoxide --version | head -n 1; then
        print "zoxide is not installed." $RED
        exit 1
    else
        print "zoxide is installed." $GREEN
    fi
}

# Run the test
zoxide_test