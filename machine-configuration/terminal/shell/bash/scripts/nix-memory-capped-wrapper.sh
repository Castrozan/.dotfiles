#!/usr/bin/env bash

resolve_real_nix_binary() {
	local candidate
	for candidate in \
		/run/current-system/sw/bin/nix \
		/nix/var/nix/profiles/default/bin/nix; do
		if [ -x "$candidate" ]; then
			printf '%s' "$candidate"
			return 0
		fi
	done
	return 1
}

real_nix_binary="$(resolve_real_nix_binary)" || {
	echo "nix-memory-capped-wrapper: real nix binary not found" >&2
	exit 127
}

if [ -n "${__NIX_MEMORY_SCOPED:-}" ] ||
	! command -v systemd-run >/dev/null 2>&1 ||
	[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
	exec "$real_nix_binary" "$@"
fi

exec systemd-run --user --scope -q \
	--setenv=__NIX_MEMORY_SCOPED=1 \
	-p MemoryHigh="${__NIX_MEMORY_HIGH:-45%}" \
	-p MemoryMax="${__NIX_MEMORY_MAX:-55%}" \
	-p MemorySwapMax="${__NIX_MEMORY_SWAP_MAX:-0}" \
	-- "$real_nix_binary" "$@"
