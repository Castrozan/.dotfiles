#!/bin/sh

# Check if nix is installed
if command -v nix >/dev/null 2>&1; then
    print "Nix already installed" "$YELLOW"
else
    print "TODO: fix nix install script" "$RED"
    print "curl -L https://nixos.org/nix/install | sh /dev/stdin" "$YELLOW"
fi
