#!/usr/bin/env bash

. "./shell/src/run_elevated_clause.sh"
. "./shell/src/is_desktop_environment.sh"
. "./shell/src/is_installed.sh"

# Install Obsidian
install_obsidian() {
    local version="1.7.7"
    local release_url="https://github.com/obsidianmd/obsidian-releases/releases/download/v${version}/obsidian_${version}_amd64.deb"
    wget "$release_url" -O /tmp/obsidian.deb

    run_elevated_clause "dpkg -i /tmp/obsidian.deb"
}

if is_desktop_environment; then
    # Check if Obsidian is installed
    if is_installed "obsidian" >/dev/null 2>&1; then
        print "Obsidian already installed" "$YELLOW"
    else
        install_obsidian
    fi
fi
