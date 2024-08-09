#!/bin/bash

# Test if tmux is installed
tmux_test() {

    if ! tmux -V; then
        print "Tmux is not installed." $RED
        exit 1
    else
        print "Tmux is installed." $GREEN
    fi
}

# Run the test
tmux_test