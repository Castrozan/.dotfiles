#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if pipes is installed
pipes_test() {

    if [ -d "$HOME/repo/pipes.sh" ]; then
        print "Pipes.sh is installed." "$_GREEN"
    else
        print "Pipes.sh is not installed." "$_RED"
        exit 1
    fi
}

# Run the test
pipes_test
