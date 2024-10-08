#!/bin/bash

. "./shell/src/run_elevated_clause.sh"
. "./shell/src/use_flatpak.sh"
use_flatpak

# Install Obsidian
install_obsidian() {
    run_elevated_clause "flatpak install flathub md.obsidian.Obsidian"
}

# Check if Obsidian is installed
if flatpak list --app | grep md.obsidian.Obsidian >/dev/null 2>&1; then
    print "Obsidian already installed" "$YELLOW"
else
    install_obsidian
fi
