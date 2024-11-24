#!/usr/bin/env bash

# Test if fzf is installed
fzf_test() {

    if fzf --version &>/dev/null; then
        print "Fzf is installed." "$GREEN"
    else
        print "Fzf is not installed." "$RED"
        exit 1
    fi
}

# Run the test
fzf_test
