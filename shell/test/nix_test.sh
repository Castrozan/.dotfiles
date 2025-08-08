#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if nix is installed
nix_test() {

    if ! which nix; then
        print "Nix is not installed." "$_RED"
        exit 1
    else
        print "Nix is installed." "$_GREEN"
    fi
}

# Run the test
nix_test
