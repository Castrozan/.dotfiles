#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/is_desktop_environment.sh"
. "./shell/src/is_installed.sh"

# Install VS Code
install_vscode() {
    local temp_dir=$(mktemp -d)

    local base_url="https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
    curl -L "${base_url}" -o "$temp_dir/vscode.deb"

    sudo dpkg -i "$temp_dir/vscode.deb"
}

if is_desktop_environment; then
    if is_installed "code" >/dev/null 2>&1; then
        print "VS Code already installed" "$_YELLOW"
    else
        install_vscode
    fi
fi
