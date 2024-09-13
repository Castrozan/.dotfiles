#!/bin/bash

# Test if nvim is installed
nvim_test() {

    if ! nvim -v >/dev/null; then
        print "Nvim is not installed." "$RED"
        exit 1
    else
        print "Nvim is installed." "$GREEN"
    fi
}

# Run the test
nvim_test
