#!/usr/bin/env bash

. "./shell/src/is_installed.sh"
. "./shell/src/print.sh"

flameshot_test() {

    if is_desktop_environment; then
        if ! is_installed flameshot; then
            print "Flameshot is not installed." "$_RED"
            exit 1
        else
            print "Flameshot is installed." "$_GREEN"
        fi
    else
        print "Desktop environment is not installed." "$_YELLOW"
    fi
}

flameshot_test
