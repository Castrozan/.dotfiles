#!/bin/bash

# Test if obsidian is installed
obsidian_test() {

    if is_desktop_environment; then
        if ! flatpak list --app | grep md.obsidian.Obsidian; then
            print "Obsidian is not installed." "$RED"
            exit 1
        else
            print "Obsidian is installed." "$GREEN"
        fi
    else
        print "Desktop enviroment is not installed." "$YELLOW"
    fi
}

# Run the test
obsidian_test
