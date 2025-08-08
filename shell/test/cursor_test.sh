#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/is_desktop_environment.sh"

# Test if Cursor is installed
cursor_test() {
    if is_desktop_environment; then
        if ! which cursor; then
            print "Cursor is not installed." "$_RED"
            exit 1
        else
            print "Cursor is installed." "$_GREEN"
        fi
    else
        print "Desktop environment is not installed." "$_YELLOW"
    fi
}

# Run the test
cursor_test 