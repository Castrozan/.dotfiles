#!/usr/bin/env bash

_bats_collection_root_directories() {
	local platformSpecificHomeDirectory
	if [[ "$(uname)" == "Darwin" ]]; then
		platformSpecificHomeDirectory="$REPO_DIR/home/darwin"
	else
		platformSpecificHomeDirectory="$REPO_DIR/home/linux"
	fi
	printf '%s\n' \
		"$REPO_DIR/home/base" \
		"$platformSpecificHomeDirectory" \
		"$REPO_DIR/agents"
}

_collect_bats_test_files_in_tier_directory() {
	local tierDirectoryName="$1"
	local rootDirectories
	mapfile -t rootDirectories < <(_bats_collection_root_directories)
	find "${rootDirectories[@]}" -path "*/__tests__/${tierDirectoryName}/*.bats" -type f 2>/dev/null | sort
}

_run_bats_tier() {
	local tierDirectoryName="$1"
	local tierLabel="$2"

	if ! command -v bats &>/dev/null; then
		echo "WARN: bats not installed, skipping bin script tests" >&2
		echo "      Install with: nix shell nixpkgs#bats" >&2
		return 0
	fi

	local testFiles
	testFiles=$(_collect_bats_test_files_in_tier_directory "$tierDirectoryName")
	if [[ -z "$testFiles" ]]; then
		return 0
	fi

	echo "--- Bin Script Tests (${tierLabel}) ---"
	bats $testFiles
	echo ""
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
