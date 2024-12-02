#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if node is installed
nodejs_test() {

    if ! node --version; then
        print "NodeJS is not installed." "$_RED"
        exit 1
    else
        print "NodeJS is installed." "$_GREEN"
    fi
}

# Run the test
nodejs_test
