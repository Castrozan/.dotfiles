#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict mode" {
    assert_strict_mode
}

@test "updates apt before installing" {
    assert_line_order "apt-get update" "apt-get install"
}

@test "installs earlyoom and zram-tools" {
    assert_installs_apt_packages earlyoom zram-tools
}

@test "configures earlyoom at 5% memory 10% swap" {
    assert_contains_all "EARLYOOM_ARGS" "-m 5" "-s 10"
}

@test "configures zram with zstd at 50% RAM" {
    assert_writes_config "/etc/default/zramswap" "ALGO=zstd" "PERCENT=50"
}

@test "sets vm.swappiness to 150" {
    assert_contains "vm.swappiness.*150"
}

@test "persists sysctl config" {
    assert_contains "sysctl.d/99-"
}

@test "activates earlyoom and zramswap services" {
    assert_activates_service earlyoom
    assert_activates_service zramswap
}

@test "handles missing systemctl gracefully" {
    assert_contains "command -v systemctl"
}
