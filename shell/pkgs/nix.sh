#!/bin/sh

# Check if nix is installed
if command -v nix >/dev/null 2>&1; then
    print "Nix already installed" "$YELLOW"
else
    install_with_custom_script_via_curl "https://nixos.org/nix/install"
fi
