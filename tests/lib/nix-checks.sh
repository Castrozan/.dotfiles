#!/usr/bin/env bash

_detect_current_system() {
	local arch
	arch="$(uname -m)"

	if [[ "$arch" == "arm64" ]]; then
		arch="aarch64"
	fi

	echo "${arch}-linux"
}

_run_nix_flake_checks() {
	if ! command -v nix &>/dev/null; then
		echo "WARN: nix not installed, skipping nix flake checks" >&2
		return 0
	fi

	local currentSystem
	currentSystem="$(_detect_current_system)"

	echo "--- Nix Flake Checks (${currentSystem}) ---"
	local checkNames
	checkNames=$(nix eval ".#checks.${currentSystem}" --apply 'builtins.attrNames' --json 2>/dev/null | jq -r '.[]')
	local failedChecks=0
	for checkName in $checkNames; do
		if nix build ".#checks.${currentSystem}.${checkName}" --no-link --print-build-logs 2>&1; then
			echo "  PASS: ${checkName}"
		else
			echo "  FAIL: ${checkName}"
			failedChecks=$((failedChecks + 1))
		fi
	done
	if [[ "$failedChecks" -gt 0 ]]; then
		echo "FAILED: ${failedChecks} check(s) failed"
		return 1
	fi
	echo ""
}
