#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/is_desktop_environment.sh"

# Test if Postman is installed
postman_test() {
    if ! snap list | grep -q "postman"; then
        print "Postman is not installed." "$_RED"
        exit 1
    else
        print "Postman is installed." "$_GREEN"
    fi
}

# Run the test
if is_desktop_environment; then
    postman_test 
fi 