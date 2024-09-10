#!/bin/sh

# Check if nix is installed
if command -v nix >/dev/null 2>&1; then
    print "Nix already installed" "$YELLOW"
else
    curl -L https://nixos.org/nix/install | yes | sh /dev/stdin
fi
