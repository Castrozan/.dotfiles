#!/usr/bin/env bats

setup() {
    SCRIPT="$BATS_TEST_DIRNAME/../../bin/setup-oom-protection"
}

@test "setup-oom-protection: script is executable" {
    [ -x "$SCRIPT" ]
}

@test "setup-oom-protection: script passes shellcheck" {
    if ! command -v shellcheck &>/dev/null; then
        skip "shellcheck not installed"
    fi
    run shellcheck "$SCRIPT"
    [ "$status" -eq 0 ]
}

@test "setup-oom-protection: uses set -euo pipefail" {
    run head -2 "$SCRIPT"
    [[ "$output" == *"set -euo pipefail"* ]]
}

@test "setup-oom-protection: installs earlyoom package" {
    run grep -c "apt install.*earlyoom" "$SCRIPT"
    [ "$output" -ge 1 ]
}

@test "setup-oom-protection: configures earlyoom with 5% memory threshold" {
    run grep "EARLYOOM_ARGS" "$SCRIPT"
    [[ "$output" == *"-m 5"* ]]
    [[ "$output" == *"-s 10"* ]]
}

@test "setup-oom-protection: enables earlyoom service" {
    run grep "systemctl enable" "$SCRIPT"
    [[ "$output" == *"earlyoom"* ]]
}

@test "setup-oom-protection: installs zram-tools" {
    run grep -c "apt install.*zram-tools" "$SCRIPT"
    [ "$output" -ge 1 ]
}

@test "setup-oom-protection: configures zram with zstd and 50% RAM" {
    run grep -A3 "zramswap" "$SCRIPT"
    [[ "$output" == *"ALGO=zstd"* ]]
    [[ "$output" == *"PERCENT=50"* ]]
}

@test "setup-oom-protection: sets vm.swappiness to 150" {
    run grep "vm.swappiness" "$SCRIPT"
    [[ "$output" == *"150"* ]]
}

@test "setup-oom-protection: persists swappiness via sysctl.d" {
    run grep "sysctl.d" "$SCRIPT"
    [[ "$output" == *"99-swappiness.conf"* ]]
}
