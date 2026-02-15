#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict error handling" {
    assert_uses_strict_error_handling
}

@test "updates apt before installing" {
    assert_pattern_appears_before "apt-get update" "apt-get install"
}

@test "installs earlyoom and zram-tools" {
    assert_installs_apt_packages earlyoom zram-tools
}

@test "configures earlyoom SIGTERM at 10% memory and SIGKILL at 5%" {
    assert_script_source_matches "EARLYOOM_SIGTERM_MEMORY_PERCENT=10"
    assert_script_source_matches "EARLYOOM_SIGTERM_SWAP_PERCENT=15"
    assert_script_source_matches "EARLYOOM_SIGKILL_MEMORY_PERCENT=5"
    assert_script_source_matches "EARLYOOM_SIGKILL_SWAP_PERCENT=5"
}

@test "configures zram with zstd at 50% RAM" {
    assert_script_source_matches "ZRAM_COMPRESSION_ALGORITHM=.zstd."
    assert_script_source_matches "ZRAM_MEMORY_PERCENT=50"
    assert_writes_config_to_path "/etc/default/zramswap"
}

@test "sets vm.swappiness to 150" {
    assert_script_source_matches "SWAPPINESS_VALUE=150"
    assert_script_source_matches "vm.swappiness"
}

@test "persists sysctl config to disk" {
    assert_script_source_matches "sysctl.d/99-"
}

@test "activates earlyoom and zramswap services" {
    assert_activates_systemd_service earlyoom
    assert_activates_systemd_service zramswap
}

@test "handles missing systemctl gracefully" {
    assert_script_source_matches "command -v systemctl"
}

@test "prefers killing nix and claude processes" {
    assert_script_source_matches_all "--prefer" "nix" "claude"
}

@test "avoids killing critical system processes" {
    assert_script_source_matches_all "--avoid" "init" "sshd" "systemd"
}
