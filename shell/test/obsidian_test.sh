#!/usr/bin/env bash

. "./shell/src/is_installed.sh"

# Test if obsidian is installed
obsidian_test() {

    if is_desktop_environment; then
        if ! is_installed obsidian &&
            exit 1
        else
            print "Obsidian is installed." "$GREEN"
        fi
    else
        print "Desktop environment is not installed." "$YELLOW"
    fi
}

# Run the test
obsidian_test
