#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if vim is installed
vim_test() {

    if ! vim --version | head -n 1; then
        print "Vim is not installed." "$_RED"
        exit 1
    else
        print "Vim is installed." "$_GREEN"
    fi
}

# Run the test
vim_test
