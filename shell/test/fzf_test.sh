#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if fzf is installed
fzf_test() {

    if fzf --version &>/dev/null; then
        print "Fzf is installed." "$_GREEN"
    else
        print "Fzf is not installed." "$_RED"
        # exit 1
    fi
}

# Run the test
fzf_test
