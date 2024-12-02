#!/usr/bin/env bash

. "./shell/src/is_installed.sh"
. "./shell/src/print.sh"

# Test if obsidian is installed
obsidian_test() {

    if is_desktop_environment; then
        if ! is_installed obsidian &&
            ! flatpak list --app | grep md.obsidian.Obsidian; then
            print "Obsidian is not installed." "$_RED"
            exit 1
        else
            print "Obsidian is installed." "$_GREEN"
        fi
    else
        print "Desktop environment is not installed." "$_YELLOW"
    fi
}

# Run the test
obsidian_test
