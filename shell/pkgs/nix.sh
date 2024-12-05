#!/usr/bin/env bash

. "./shell/src/install_with_temp_custom_script.sh"

install_nix() {
    # Check if nix is installed
    if command -v nix >/dev/null 2>&1; then
        print "Nix already installed" "$_YELLOW"
    else
        install_with_temp_custom_script "https://nixos.org/nix/install"
        # TODO: set up nix channels like
        #   nix-channel --add https://channels.nixos.org/nixos-24.05 nixpkgs
        #   nix-channel --update
    fi
}

# Install nix
# install_nix
# TODO: fix nix install
