#!/usr/bin/env bash

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
