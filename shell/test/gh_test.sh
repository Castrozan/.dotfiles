#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if GitHub CLI is installed
gh_test() {
    if ! gh --version | head -n 1; then
        print "GitHub CLI is not installed." "$_RED"
        exit 1
    else
        print "GitHub CLI is installed." "$_GREEN"
    fi
}

# Run the test
gh_test 