#!/usr/bin/env bash

_collect_bats_test_files_in_tier_directory() {
	local tierDirectoryName="$1"
	_discover_test_files "platform-scoped" "*/__tests__/${tierDirectoryName}/*.bats"
}

_run_bats_tier() {
	local tierDirectoryName="$1"
	local tierLabel="$2"

	if ! command -v bats &>/dev/null; then
		echo "WARN: bats not installed, skipping bin script tests" >&2
		echo "      Install with: nix shell nixpkgs#bats" >&2
		return 0
	fi

	local -a testFiles
	mapfile -t testFiles < <(_collect_bats_test_files_in_tier_directory "$tierDirectoryName")
	if [[ ${#testFiles[@]} -eq 0 ]]; then
		return 0
	fi

	echo "--- Bin Script Tests (${tierLabel}) ---"
	local batsExitCode=0
	bats "${testFiles[@]}" || batsExitCode=$?
	echo ""
	return "$batsExitCode"
}

_run_quick_bats_tests() {
	_run_bats_tier "unit" "quick"
}

_run_quick_bats_tests_ci() {
	_run_bats_tier "unit" "ci"
}

_run_integration_scripts_bats_tests() {
	_run_bats_tier "integration" "integration-scripts"
}

_run_e2e_scripts_bats_tests() {
	_run_bats_tier "e2e" "e2e-scripts"
}

_run_bats_with_coverage() {
	if ! command -v kcov &>/dev/null || ! command -v bats &>/dev/null; then
		echo "WARN: kcov or bats not installed, skipping coverage" >&2
		echo "      Install with: nix shell nixpkgs#kcov nixpkgs#bats" >&2
		return 0
	fi

	echo "--- Bin Script Tests with Coverage ---"
	"$SCRIPT_DIR/cover/bash-coverage.sh"
	echo ""
}
