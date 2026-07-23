#!/usr/bin/env bash

_collect_pytest_test_files_in_tier_directory() {
	local tierDirectoryName="$1"
	_discover_test_files "platform-scoped" "*/__tests__/${tierDirectoryName}/test_*.py"
}

_run_pytest_tier() {
	local tierDirectoryName="$1"
	local tierLabel="$2"

	local -a testFiles
	mapfile -t testFiles < <(_collect_pytest_test_files_in_tier_directory "$tierDirectoryName")
	if [[ ${#testFiles[@]} -eq 0 ]]; then
		return 0
	fi

	if ! command -v pytest &>/dev/null; then
		echo "ERROR: ${tierLabel} python tests were collected but pytest is not installed; refusing to skip silently" >&2
		return 1
	fi

	echo "--- Python Tests (${tierLabel}) ---"
	local pytestExitCode=0
	pytest "${testFiles[@]}" -q || pytestExitCode=$?
	echo ""
	return "$pytestExitCode"
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
