#!/usr/bin/env bash

_collect_pytest_test_files_in_tier_directory() {
	local tierDirectoryName="$1"
	_discover_test_files "platform-scoped" "*/__tests__/${tierDirectoryName}/*" "test_*.py"
}

_run_pytest_tier() {
	local tierDirectoryName="$1"
	local tierLabel="$2"

	local -a testFiles=()
	local discoveredTestFile
	while IFS= read -r discoveredTestFile; do
		testFiles+=("$discoveredTestFile")
	done < <(_collect_pytest_test_files_in_tier_directory "$tierDirectoryName")
	local reportSuffix=''
	if [[ -n "${DOTFILES_PYTEST_SHARD_INDEX+set}" || -n "${DOTFILES_PYTEST_SHARD_COUNT+set}" ]]; then
		local selectedTestFiles
		selectedTestFiles=$(python3 "${BASH_SOURCE[0]%/*}/pytest_shards.py" "$REPO_DIR" \
			"${DOTFILES_PYTEST_SHARD_INDEX:-}" "${DOTFILES_PYTEST_SHARD_COUNT:-}" "${testFiles[@]}") || return
		testFiles=()
		if [[ -n "$selectedTestFiles" ]]; then
			while IFS= read -r discoveredTestFile; do
				testFiles+=("$discoveredTestFile")
			done <<<"$selectedTestFiles"
		fi
		reportSuffix="-shard-${DOTFILES_PYTEST_SHARD_INDEX}-of-${DOTFILES_PYTEST_SHARD_COUNT}"
	fi
	if [[ ${#testFiles[@]} -eq 0 ]]; then
		return 0
	fi

	if ! command -v pytest &>/dev/null; then
		echo "ERROR: ${tierLabel} python tests were collected but pytest is not installed; refusing to skip silently" >&2
		return 1
	fi

	echo "--- Python Tests (${tierLabel}) ---"
	local -a report_arguments=()
	if [[ -n "${DOTFILES_TEST_REPORT_DIRECTORY:-}" ]]; then
		mkdir -p "$DOTFILES_TEST_REPORT_DIRECTORY" || return
		report_arguments=("--junitxml=${DOTFILES_TEST_REPORT_DIRECTORY}/pytest-${tierDirectoryName}${reportSuffix}.xml")
	fi
	local pytestExitCode=0
	DOTFILES_TEST_REPORT_DIRECTORY='' pytest "${report_arguments[@]}" "${testFiles[@]}" -q || pytestExitCode=$?
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
