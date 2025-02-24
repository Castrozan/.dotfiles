#!/usr/bin/env bash

. "./shell/src/is_installed.sh"
. "./shell/src/print.sh"

warp_test() {

    if is_desktop_environment; then
        if ! is_installed warp-terminal; then
            print "Warp is not installed." "$_RED"
            exit 1
        else
            print "Warp is installed." "$_GREEN"
        fi
    else
        print "Desktop environment is not installed." "$_YELLOW"
    fi
}

warp_test
