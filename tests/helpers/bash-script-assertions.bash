#!/usr/bin/env bash

readonly DOTFILES_BIN_DIRECTORY="$BATS_TEST_DIRNAME/../../bin"

_resolve_script_under_test() {
    local testFileName="${BATS_TEST_FILENAME##*/}"
    testFileName="${testFileName%.bats}"
    echo "$DOTFILES_BIN_DIRECTORY/$testFileName"
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
    [ "$status" -eq 0 ]
}

assert_uses_strict_error_handling() {
    run head -5 "$(_resolve_script_under_test)"
    [[ "$output" == *"set -euo pipefail"* ]]
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
