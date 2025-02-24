#!/usr/bin/env bash

. "./shell/src/run_elevated_clause.sh"
. "./shell/src/is_desktop_environment.sh"
. "./shell/src/is_installed.sh"

install_warp() {
    local version="0.2025.02.19.08.02.stable"
    local release="05"
    local url="https://releases.warp.dev/stable/v${version}_${release}/warp-terminal_${version}.${release}_amd64.deb"
    wget "$url" -O /tmp/warp.deb

    sudo dpkg -i /tmp/warp.deb
}

if is_desktop_environment; then
    if is_installed "warp" >/dev/null 2>&1; then
        print "Warp already installed" "$_YELLOW"
    else
        install_warp
    fi
fi
