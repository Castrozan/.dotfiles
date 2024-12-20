#!/usr/bin/env bash

# Install a package with a custom script via a networking tool
# $1: URI to download the custom script
# $2: Networking tool to use (default: curl)
# $3: Flags to pass to the tool (default for curl: -L)
# $4: Shell to run the script (default: sh)
# $5: Shell flags to pass to the shell (default: none)
# Works like this: "$tool" "$flags" "$uri" "$tmpFile"
install_with_sh() {
    shell="${1:-sh}"
    tool="${2:-curl}"
    flags="${3:--L}"
    uri="$4"
    shellFlags="${5:-}"

    # sh <(curl -L https://nixos.org/nix/install) --no-daemon --yes --no-channel-add
    echo "$shell <($tool $flags $uri) $shellFlags"
    # shellcheck disable=SC2086
    $shell <($tool $flags $uri) $shellFlags
}
