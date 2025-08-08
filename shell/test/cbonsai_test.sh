#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if cbonsai is installed
cbonsai_test() {

    if ! which cbonsai; then
        print "Cbonsai is not installed." "$_RED"
        exit 1
    else
        print "Cbonsai is installed." "$_GREEN"
    fi
}

# Run the test
cbonsai_test
