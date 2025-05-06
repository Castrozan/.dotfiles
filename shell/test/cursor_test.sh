#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if Cursor is installed
cursor_test() {
    if [ ! -f "$HOME/.local/bin/cursor" ]; then
        print "Cursor is not installed." "$_RED"
        exit 1
    else
        print "Cursor is installed." "$_GREEN"
    fi
}

# Run the test
cursor_test 