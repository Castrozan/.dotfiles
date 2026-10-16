#!/usr/bin/env bash

_collect_bats_test_files_in_tier_directory() {
	local tierDirectoryName="$1"
	_discover_test_files "platform-scoped" "*/__tests__/${tierDirectoryName}/*" "*.bats"
}

_run_bats_tier() {
	local tierDirectoryName="$1"
	local tierLabel="$2"
	local coverageOutputDirectory="${3:-}"

	if ! command -v bats &>/dev/null; then
		echo "WARN: bats not installed, skipping bin script tests" >&2
		echo "      Install with: nix shell nixpkgs#bats" >&2
		return 0
	fi

	local -a testFiles=()
	local discoveredTestFile
	while IFS= read -r discoveredTestFile; do
		testFiles+=("$discoveredTestFile")
	done < <(_collect_bats_test_files_in_tier_directory "$tierDirectoryName")
	if [[ ${#testFiles[@]} -eq 0 ]]; then
		return 0
	fi

	echo "--- Bin Script Tests (${tierLabel}) ---"
	local -a report_arguments=()
	if [[ -n "${DOTFILES_TEST_REPORT_DIRECTORY:-}" ]]; then
		local report_directory="${DOTFILES_TEST_REPORT_DIRECTORY}/bats-${tierDirectoryName}"
		mkdir -p "$report_directory" || return
		report_arguments=(--report-formatter junit --output "$report_directory")
	fi
	local -a batsCommand=(bats)
	if [[ -n "$coverageOutputDirectory" ]]; then
		batsCommand=(
			kcov
			"--bash-parser=$BASH"
			--bash-dont-parse-binary-dir
			"--include-pattern=$REPO_DIR/machine-configuration/"
			"$coverageOutputDirectory"
			bats
		)
	fi
	local batsExitCode=0
	DOTFILES_TEST_REPORT_DIRECTORY='' "${batsCommand[@]}" "${report_arguments[@]}" "${testFiles[@]}" || batsExitCode=$?
	echo ""
	return "$batsExitCode"
}

_run_quick_bats_tests() {
	_run_bats_tier "unit" "quick"
}

_run_quick_bats_tests_ci() {
	local coverageExitCode=0
	"$SCRIPT_DIR/cover/bash-coverage.sh" --ci || coverageExitCode=$?
	return "$coverageExitCode"
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
