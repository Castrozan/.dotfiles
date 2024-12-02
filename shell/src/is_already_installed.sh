#!/usr/bin/env bash

. "./shell/src/print.sh"

# is_already_installed.sh
# function to print that a package is already installed
# $1: package name
is_already_installed() {
    local pkg=$1

    print "$pkg is already installed." "$_YELLOW"
}
