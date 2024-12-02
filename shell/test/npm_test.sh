#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if npm is installed
npm_test() {

    if ! npm --version; then
        print "Npm is not installed." "$_RED"
        exit 1
    else
        print "Npm is installed." "$_GREEN"
    fi
}

# Run the test
npm_test
