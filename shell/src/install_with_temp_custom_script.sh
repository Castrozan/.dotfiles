#!/bin/sh

# Install a package with a custom script via a networking tool
# $1: URI to download the custom script
# $2: Networking tool to use (default: curl)
# $3: Flags to pass to the tool (default for curl: -L)
# $4: Shell to run the script (default: sh)
# Works like this: "$tool" "$flags" "$uri" "$tmpFile"
install_with_temp_custom_script() {
    uri="$1"
    tool="${2:-curl}"
    flags="${3:--L}"
    shell="${4:-sh}"

    # Create a temporary file
    tmpFile=$(mktemp)

    # Send the script to the temporary file
    echo "$tool" "$flags" "$uri" >"$tmpFile"
    "$tool" "$flags" "$uri" >"$tmpFile"

    # Execute the script stored in the temporary file
    "$shell" "$tmpFile"

    # Clean up the temporary file
    rm "$tmpFile"
}
