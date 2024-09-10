#!/bin/bash

# Test if nix is installed
nix_test() {

    if ! nix --help >/dev/null 2>&1; then
        print "Nix is not installed." "$RED"
        exit 1
    else
        print "Nix is installed." "$GREEN"
    fi
}

# Run the test
nix_test
