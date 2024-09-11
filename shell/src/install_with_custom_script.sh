#!/bin/sh

# Install a package with a custom script via curl
# $1: uri to download custom script
install_with_custom_script_via_curl() {
    _uri="$1"

    # Create a temporary file
    tmp="$(mktemp)"

    # Send the script to the temporary file
    curl -L "$1" >"$tmp"

    # Execute the script stored in the temporary file
    sh "$tmp"

    # Clean up the temporary file
    rm "$tmp"
}
