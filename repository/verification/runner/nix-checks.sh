#!/usr/bin/env bash

_detect_nix_system_double_from_kernel_and_machine() {
	local nixArchFromUnameMachine
	case "$(uname -m)" in
	arm64 | aarch64) nixArchFromUnameMachine="aarch64" ;;
	x86_64 | amd64) nixArchFromUnameMachine="x86_64" ;;
	*) nixArchFromUnameMachine="$(uname -m)" ;;
	esac

	local nixKernelSuffixFromUnameKernel
	case "$(uname -s)" in
	Darwin) nixKernelSuffixFromUnameKernel="darwin" ;;
	Linux) nixKernelSuffixFromUnameKernel="linux" ;;
	*) nixKernelSuffixFromUnameKernel="$(uname -s | tr '[:upper:]' '[:lower:]')" ;;
	esac

	echo "${nixArchFromUnameMachine}-${nixKernelSuffixFromUnameKernel}"
}

_flake_exposes_checks_for_system() {
	local nixSystemDouble="$1"
	nix eval ".#checks.${nixSystemDouble}" --apply 'cs: builtins.attrNames cs' --json >/dev/null 2>&1
}

_run_nix_flake_checks() {
	if ! command -v nix &>/dev/null; then
		echo "WARN: nix not installed, skipping nix flake checks" >&2
		return 0
	fi

	local currentSystem
	currentSystem="$(_detect_nix_system_double_from_kernel_and_machine)"

	echo "--- Nix Flake Checks (${currentSystem}) ---"

	if ! _flake_exposes_checks_for_system "${currentSystem}"; then
		echo "SKIP: flake does not expose checks.${currentSystem} (only checks for other systems are defined)"
		echo ""
		return 0
	fi

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
