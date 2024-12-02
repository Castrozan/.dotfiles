#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if zoxide is installed
zoxide_test() {

    if ! zoxide --version | head -n 1; then
        print "zoxide is not installed." "$_RED"
        exit 1
    else
        print "zoxide is installed." "$_GREEN"
    fi
}

# Run the test
zoxide_test
