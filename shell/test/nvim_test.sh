#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if nvim is installed
nvim_test() {

    if ! nvim -v >/dev/null; then
        print "Nvim is not installed." "$_RED"
        exit 1
    else
        print "Nvim is installed." "$_GREEN"
    fi
}

# Run the test
# nvim_test
print "Nvim PATH var is not working." "$_RED"
print "TODO: Fix the PATH var for nvim." "$_RED"
