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

@test "configures TCP buffer max to 16 MB" {
    assert_script_source_matches "TCP_BUFFER_MAX=16777216"
}

@test "configures TCP buffer default to 1 MB" {
    assert_script_source_matches "TCP_BUFFER_DEFAULT=1048576"
}

@test "enables BBR congestion control" {
    assert_script_source_matches "TCP_CONGESTION_CONTROL=.bbr."
    assert_script_source_matches "tcp_congestion_control"
}

@test "uses fq queue discipline for BBR" {
    assert_script_source_matches "TCP_QUEUE_DISCIPLINE=.fq."
    assert_script_source_matches "default_qdisc"
}

@test "enables TCP Fast Open for client and server" {
    assert_script_source_matches "TCP_FAST_OPEN_CLIENT_AND_SERVER=3"
    assert_script_source_matches "tcp_fastopen"
}

@test "disables TCP slow start after idle" {
    assert_script_source_matches "tcp_slow_start_after_idle = 0"
}

@test "enables TCP MTU probing" {
    assert_script_source_matches "tcp_mtu_probing = 1"
}

@test "increases netdev backlog queue" {
    assert_script_source_matches "NETDEV_MAX_BACKLOG=16384"
    assert_script_source_matches "netdev_max_backlog"
}

@test "persists sysctl config to disk" {
    assert_script_source_matches "sysctl.d/99-network-optimization.conf"
}

@test "disables WiFi power management via NetworkManager" {
    assert_script_source_matches "wifi.powersave = 2"
    assert_script_source_matches "/etc/NetworkManager/conf.d/"
}

@test "configures Cloudflare DNS-over-TLS" {
    assert_script_source_matches "1.1.1.1#cloudflare-dns.com"
    assert_script_source_matches "1.0.0.1#cloudflare-dns.com"
    assert_script_source_matches "DNSOverTLS=yes"
}

@test "writes resolved config to systemd directory" {
    assert_script_source_matches "resolved.conf.d"
}

@test "handles missing systemctl gracefully" {
    assert_script_source_matches "command -v systemctl"
}

@test "handles missing iwconfig gracefully" {
    assert_script_source_matches "command -v iwconfig"
}

@test "initializes sysctl config before writing" {
    assert_pattern_appears_before "_initialize_sysctl_config_file" "_configure_tcp_buffer_sizes"
}
