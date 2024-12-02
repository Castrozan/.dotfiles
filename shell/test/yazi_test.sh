#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if Yazi is installed
yazi_test() {

    if ! yazi --version | head -n 1; then
        print "Yazi is not installed." "$_RED"
        exit 1
    else
        print "Yazi is installed." "$_GREEN"
    fi
}

# Run the test
yazi_test
