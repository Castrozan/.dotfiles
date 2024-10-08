#!/bin/bash

# Test if obsidian is installed
obsidian_test() {

    if ! flatpak list --app | grep md.obsidian.Obsidian; then
        print "Obsidian is not installed." "$RED"
        exit 1
    else
        print "Obsidian is installed." "$GREEN"
    fi
}

# Run the test
obsidian_test
