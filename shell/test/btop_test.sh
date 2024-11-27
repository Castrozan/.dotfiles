#!/usr/bin/env bash

# Test if btop is installed
btop_test() {

    if ! btop --version; then
        print "Btop is not installed." "$_RED"
        exit 1
    else
        print "Btop is installed." "$_GREEN"
    fi
}

# Run the test
btop_test
