#!/bin/bash

. "shell/src/print.sh"

# Test if kitty is installed
kitty_test() {

    if ! kitty --help >/dev/null 2>&1; then
        print "Kitty is not installed." "$RED"
        exit 1
    else
        print "Kitty is installed." "$GREEN"
    fi
}

# Run the test
# kitty_test
print "TODO: fix kitty_test" "$RED"
