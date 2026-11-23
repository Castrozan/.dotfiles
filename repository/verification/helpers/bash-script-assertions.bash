#!/usr/bin/env bash

readonly DOTFILES_ROOT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
readonly DOTFILES_BIN_DIRECTORY="$DOTFILES_ROOT_DIRECTORY/bin"
readonly DOTFILES_HOME_BASE_DIRECTORY="$DOTFILES_ROOT_DIRECTORY/home/base"
readonly DOTFILES_HOME_LINUX_DIRECTORY="$DOTFILES_ROOT_DIRECTORY/home/linux"
readonly DOTFILES_MACHINE_CONFIGURATION_DIRECTORY="$DOTFILES_ROOT_DIRECTORY/machine-configuration"
readonly DOTFILES_SKILLS_DIRECTORY="$DOTFILES_ROOT_DIRECTORY/agent-harness/agent-instructions/skills"

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
	domainScriptMatch=$(find \
		"$DOTFILES_HOME_BASE_DIRECTORY" \
		"$DOTFILES_HOME_LINUX_DIRECTORY" \
		"$DOTFILES_MACHINE_CONFIGURATION_DIRECTORY" \
		-type f -name "$testFileName" -path "*/scripts/*" 2>/dev/null | head -1)
	if [ -n "$domainScriptMatch" ]; then
		echo "$domainScriptMatch"
		return
	fi
	local skillScriptMatch
	skillScriptMatch=$(find "$DOTFILES_SKILLS_DIRECTORY" -type f -name "$testFileName" -path "*/scripts/*" 2>/dev/null | head -1)
	if [ -n "$skillScriptMatch" ]; then
		echo "$skillScriptMatch"
		return
	fi
	echo "$legacyBinPath"
}

run_script_under_test() {
	run "$(_resolve_script_under_test)" "$@"
}

assert_fails_with() {
	local expectedOutputPattern="$1"
	shift
	run_script_under_test "$@"
	# shellcheck disable=SC2154
	[ "$status" -ne 0 ]
	# shellcheck disable=SC2154
	[[ "$output" == *"$expectedOutputPattern"* ]]
}

assert_succeeds_with() {
	local expectedOutputPattern="$1"
	shift
	run_script_under_test "$@"
	[ "$status" -eq 0 ]
	[[ "$output" == *"$expectedOutputPattern"* ]]
}
