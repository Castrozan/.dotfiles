#!/usr/bin/env bash

# Check if nix is installed
if command -v nix >/dev/null 2>&1; then
    print "Nix already installed" "$YELLOW"
else
    install_with_temp_custom_script "https://nixos.org/nix/install"
fi
