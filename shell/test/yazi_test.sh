#!/bin/bash

# Test if Yazi is installed
yazi_test() {

    if ! yazi --version | head -n 1; then
        print "Yazi is not installed." "$RED"
        exit 1
    else
        print "Yazi is installed." "$GREEN"
    fi
}

# Run the test
yazi_test
