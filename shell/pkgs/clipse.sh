#!/usr/bin/env bash

. "./shell/src/should_install.sh"

# Install clipse with nix
install_clipse() {

    if ! command -v nix >/dev/null 2>&1; then
        print "Nix should be installed for Clipse" "$_RED"
        print "Skipping Clipse installation" "$_YELLOW" "$_BOLD"
        print "Follow instructions on https://github.com/savedra1/clipse" "$_YELLOW"
    else
        should_install clipse nix
    fi
}

install_clipse
