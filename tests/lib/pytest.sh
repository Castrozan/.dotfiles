#!/usr/bin/env bash

_pytest_collection_root_directories() {
	local platformSpecificHomeDirectory
	if [[ "$(uname)" == "Darwin" ]]; then
		platformSpecificHomeDirectory="$REPO_DIR/home/darwin"
	else
		platformSpecificHomeDirectory="$REPO_DIR/home/linux"
	fi
	printf '%s\n' \
		"$REPO_DIR/home/base" \
		"$platformSpecificHomeDirectory" \
		"$REPO_DIR/agents/evals" \
		"$REPO_DIR/agents/hooks" \
		"$REPO_DIR/agents/skills" \
		"$REPO_DIR/agents/usage" \
		"$REPO_DIR/nixos" \
		"$REPO_DIR/tests"
}

_collect_pytest_test_files_in_tier_directory() {
	local tierDirectoryName="$1"
	local rootDirectories
	mapfile -t rootDirectories < <(_pytest_collection_root_directories)
	find "${rootDirectories[@]}" -path "*/tests/${tierDirectoryName}/test_*.py" -type f 2>/dev/null | sort
}

_run_pytest_tier() {
	local tierDirectoryName="$1"
	local tierLabel="$2"

	local testFiles
	testFiles=$(_collect_pytest_test_files_in_tier_directory "$tierDirectoryName")
	if [[ -z "$testFiles" ]]; then
		return 0
	fi

	if ! command -v pytest &>/dev/null; then
		echo "ERROR: ${tierLabel} python tests were collected but pytest is not installed; refusing to skip silently" >&2
		return 1
	fi

	echo "--- Python Tests (${tierLabel}) ---"
	pytest $testFiles -x -q
	echo ""
}

_run_quick_pytest_tests() {
	_run_pytest_tier "unit" "quick"
}

_run_integration_scripts_pytest_tests() {
	_run_pytest_tier "integration" "integration-scripts"
}

_run_e2e_scripts_pytest_tests() {
	_run_pytest_tier "e2e" "e2e-scripts"
}
