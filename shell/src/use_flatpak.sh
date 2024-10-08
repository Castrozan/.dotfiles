#!/bin/bash

. "./shell/src/should_install.sh"

# Function to install flatpack
use_flatpak() {
    should_install flatpak

    if flatpak --version >/dev/null 2>&1; then
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    fi
}
