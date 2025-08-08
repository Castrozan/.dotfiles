#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if clipse is installed
clipse_test() {

    if ! which clipse; then
        print "Clipse is not installed." "$_RED"
        exit 1
    else
        print "Clipse is installed." "$_GREEN"
    fi
}

# Run the test
clipse_test
