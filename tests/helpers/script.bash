#!/usr/bin/env bash

BIN_DIR="$BATS_TEST_DIRNAME/../../bin"

script_under_test() {
    local scriptName="${BATS_TEST_FILENAME##*/}"
    scriptName="${scriptName%.bats}"
    echo "$BIN_DIR/$scriptName"
}

assert_is_executable() {
    [ -x "$(script_under_test)" ]
}

assert_passes_shellcheck() {
    if ! command -v shellcheck &>/dev/null; then
        skip "shellcheck not installed"
    fi
    run shellcheck "$(script_under_test)"
    [ "$status" -eq 0 ]
}

assert_strict_mode() {
    run head -5 "$(script_under_test)"
    [[ "$output" == *"set -euo pipefail"* ]]
}

assert_contains() {
    local pattern="$1"
    run grep -E -- "$pattern" "$(script_under_test)"
    [ "$status" -eq 0 ]
}

assert_contains_all() {
    for pattern in "$@"; do
        assert_contains "$pattern"
    done
}

assert_line_order() {
    local firstPattern="$1"
    local secondPattern="$2"
    local script
    script="$(script_under_test)"
    local firstLine secondLine
    firstLine=$(grep -n -m1 -- "$firstPattern" "$script" | cut -d: -f1)
    secondLine=$(grep -n -m1 -- "$secondPattern" "$script" | cut -d: -f1)
    [ -n "$firstLine" ] && [ -n "$secondLine" ] && [ "$firstLine" -lt "$secondLine" ]
}

assert_installs_apt_packages() {
    for pkg in "$@"; do
        assert_contains "apt-get install.*$pkg"
    done
}

assert_writes_config() {
    local configPath="$1"
    shift
    assert_contains "$configPath"
    for value in "$@"; do
        assert_contains "$value"
    done
}

assert_activates_service() {
    local serviceName="$1"
    assert_contains "activate_service.*$serviceName|systemctl.*enable.*$serviceName"
}
