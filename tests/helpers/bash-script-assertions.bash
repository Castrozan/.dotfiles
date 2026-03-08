#!/usr/bin/env bash

readonly DOTFILES_ROOT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly DOTFILES_BIN_DIRECTORY="$DOTFILES_ROOT_DIRECTORY/bin"
readonly DOTFILES_MODULES_DIRECTORY="$DOTFILES_ROOT_DIRECTORY/home/modules"

_resolve_script_under_test() {
	if [ -n "${SCRIPT_UNDER_TEST:-}" ]; then
		echo "$SCRIPT_UNDER_TEST"
		return
	fi
	local testFileName="${BATS_TEST_FILENAME##*/}"
	testFileName="${testFileName%.bats}"
	local legacyBinPath="$DOTFILES_BIN_DIRECTORY/$testFileName"
	if [ -f "$legacyBinPath" ]; then
		echo "$legacyBinPath"
		return
	fi
	local domainScriptMatch
	domainScriptMatch=$(find "$DOTFILES_MODULES_DIRECTORY" -type f -name "$testFileName" -path "*/scripts/*" 2>/dev/null | head -1)
	if [ -n "$domainScriptMatch" ]; then
		echo "$domainScriptMatch"
		return
	fi
	echo "$legacyBinPath"
}

run_script_under_test() {
	run "$(_resolve_script_under_test)" "$@"
}

assert_is_executable() {
	[ -x "$(_resolve_script_under_test)" ]
}

assert_passes_shellcheck() {
	if ! command -v shellcheck &>/dev/null; then
		skip "shellcheck not installed"
	fi
	run shellcheck "$(_resolve_script_under_test)"
	# shellcheck disable=SC2154
	[ "$status" -eq 0 ]
}

assert_uses_strict_error_handling() {
	run head -5 "$(_resolve_script_under_test)"
	# shellcheck disable=SC2154
	[[ "$output" == *"set -Eeuo pipefail"* ]] || [[ "$output" == *"set -euo pipefail"* ]]
}

assert_fails_with() {
	local expectedOutputPattern="$1"
	shift
	run_script_under_test "$@"
	[ "$status" -ne 0 ]
	[[ "$output" == *"$expectedOutputPattern"* ]]
}

assert_succeeds_with() {
	local expectedOutputPattern="$1"
	shift
	run_script_under_test "$@"
	[ "$status" -eq 0 ]
	[[ "$output" == *"$expectedOutputPattern"* ]]
}

assert_script_source_matches() {
	local pattern="$1"
	run grep -E -- "$pattern" "$(_resolve_script_under_test)"
	[ "$status" -eq 0 ]
}

assert_script_source_matches_all() {
	for pattern in "$@"; do
		assert_script_source_matches "$pattern"
	done
}

assert_pattern_appears_before() {
	local firstPattern="$1"
	local secondPattern="$2"
	local scriptPath
	scriptPath="$(_resolve_script_under_test)"
	local firstLineNumber secondLineNumber
	firstLineNumber=$(grep -n -m1 -- "$firstPattern" "$scriptPath" | cut -d: -f1)
	secondLineNumber=$(grep -n -m1 -- "$secondPattern" "$scriptPath" | cut -d: -f1)
	[ -n "$firstLineNumber" ] && [ -n "$secondLineNumber" ] && [ "$firstLineNumber" -lt "$secondLineNumber" ]
}

assert_installs_apt_packages() {
	for packageName in "$@"; do
		assert_script_source_matches "apt-get install.*$packageName"
	done
}

assert_writes_config_to_path() {
	local configFilePath="$1"
	shift
	assert_script_source_matches "$configFilePath"
	for expectedValue in "$@"; do
		assert_script_source_matches "$expectedValue"
	done
}

assert_activates_systemd_service() {
	local serviceName="$1"
	assert_script_source_matches "activate_service.*$serviceName|systemctl.*enable.*$serviceName"
}
