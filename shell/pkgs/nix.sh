#!/usr/bin/env bash

. "./shell/src/install_with_temp_custom_script.sh"

install_nix() {
    # Check if nix is installed
    if nix --version >/dev/null 2>&1; then
        print "Nix already installed" "$_YELLOW"
    else
        install_with_temp_custom_script "https://nixos.org/nix/install" "curl" \
            "-L" "sh" "--no-daemon --yes --no-channel-add"
    fi
}

# Install nix
install_nix
