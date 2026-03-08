#!/usr/bin/env bash

__NIX_MEMORY_LIMIT="16G"

if [ -z "${__NIX_REAL_BINARY_PATH:-}" ] && command -v nix >/dev/null 2>&1; then
  __NIX_REAL_BINARY_PATH="$(command -v nix)"
fi

if [ -n "${__NIX_REAL_BINARY_PATH:-}" ]; then
  nix() {
    if command -v systemd-run >/dev/null 2>&1 && [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
      systemd-run --user --scope -q \
        -p MemoryMax="$__NIX_MEMORY_LIMIT" \
        -- "$__NIX_REAL_BINARY_PATH" "$@"
    else
      "$__NIX_REAL_BINARY_PATH" "$@"
    fi
  }
fi
