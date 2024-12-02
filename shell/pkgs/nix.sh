#!/usr/bin/env bash

. "./shell/src/install_with_temp_custom_script.sh"

# Check if nix is installed
if command -v nix >/dev/null 2>&1; then
    print "Nix already installed" "$_YELLOW"
else
    install_with_temp_custom_script "https://nixos.org/nix/install"
fi
