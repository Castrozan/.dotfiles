#!/bin/bash

# Test if btop is installed
btop_test() {

    if ! btop --version; then
        print "Btop is not installed." "$RED"
        exit 1
    else
        print "Btop is installed." "$GREEN"
    fi
}

# Run the test
btop_test
