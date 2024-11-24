#!/bin/bash

# Test if bat is installed
bat_test() {

    if ! bat --version; then
        print "Bat is not installed." "$RED"
        exit 1
    else
        print "Bat is installed." "$GREEN"
    fi
}

# Run the test
bat_test
