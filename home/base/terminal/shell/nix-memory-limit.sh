#!/usr/bin/env bash

__NIX_MEMORY_HIGH="45%"
__NIX_MEMORY_MAX="55%"
__NIX_MEMORY_SWAP_MAX="0"

if [ -z "${__NIX_REAL_BINARY_PATH:-}" ] && command -v nix >/dev/null 2>&1; then
	__NIX_REAL_BINARY_PATH="$(command -v nix)"
fi

if [ -n "${__NIX_REAL_BINARY_PATH:-}" ]; then
	nix() {
		if command -v systemd-run >/dev/null 2>&1 && [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
			systemd-run --user --scope -q \
				-p MemoryHigh="$__NIX_MEMORY_HIGH" \
				-p MemoryMax="$__NIX_MEMORY_MAX" \
				-p MemorySwapMax="$__NIX_MEMORY_SWAP_MAX" \
				-- "$__NIX_REAL_BINARY_PATH" "$@"
		else
			"$__NIX_REAL_BINARY_PATH" "$@"
		fi
	}
fi
