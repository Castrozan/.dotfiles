#!/usr/bin/env bash

# Function for cbonsai
bonsai() {
    if grep -q "ID=nixos" /etc/os-release; then
        # NixOS case
        cbonsai "$@"
    else
        # Ubuntu case
        "$HOME/repo/cbonsai/cbonsai" "$@"
    fi
}

# Function for pipes.sh
# shellcheck disable=SC2120
pipes() {
    if grep -q "ID=nixos" /etc/os-release; then
        # NixOS case
        pipes.sh "$@"
    else
        # Ubuntu case
        "$HOME/repo/pipes.sh/pipes.sh" "$@"
    fi
}

# Function for pipes as screensaver
pipes_screensaver() {
    pipes
}

# Function for cbonsai as screensaver
bonsai_screensaver() {
    bonsai -l -i -b 1 -c mWm,wMw,mMw,wWm -M 3 -L 40
}
