#!/usr/bin/env bash

# Test if tmux is installed
tmux_test() {

    if ! tmux -V >/dev/null; then
        print "Tmux is not installed." "$_RED"
        exit 1
    else
        print "Tmux is installed." "$_GREEN"
    fi
}

# Run the test
tmux_test
