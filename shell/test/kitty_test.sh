#!/usr/bin/env bash

. "shell/src/print.sh"
. "./shell/src/is_desktop_environment.sh"

kitty_test() {
    if is_desktop_environment; then
        if ! kitty --help >/dev/null 2>&1; then
            print "Kitty is not installed." "$_RED"
            exit 1
        else
            print "Kitty is installed." "$_GREEN"
        fi
    fi
}

kitty_test
