#!/bin/sh

# Check if nix is installed
if command -v nix >/dev/null 2>&1; then
    print "Nix already installed" "$YELLOW"
else
    # Create a temporary file
    tmp="$(mktemp)"

    # Download the Nix install script and store it in the temporary file
    curl -L https://nixos.org/nix/install >"$tmp"

    # Execute the script stored in the temporary file
    sh "$tmp" --daemon

    # Clean up the temporary file
    rm "$tmp"
fi
