#!/usr/bin/env bash

# Test if cbonsai is installed
cbonsai_test() {

    if [ -d "$HOME/repo/cbonsai" ]; then
        print "Cbonsai is installed." "$_GREEN"
    else
        print "Cbonsai is not installed." "$_RED"
        exit 1
    fi
}

# Run the test
cbonsai_test
