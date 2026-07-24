#!/usr/bin/env bats

load '../../../../../__tests__/helpers/docker-container-assertions'

readonly DOCKER_IMAGE_TAG="dotfiles-network-test"
readonly SCRIPT_PATH_INSIDE_CONTAINER="/dotfiles/home/base/network/scripts/setup-network-optimization"
readonly SYSCTL_NETWORK_CONFIG_PATH="/etc/sysctl.d/99-network-optimization.conf"
readonly NETWORKMANAGER_WIFI_POWERSAVE_CONFIG_PATH="/etc/NetworkManager/conf.d/wifi-powersave-off.conf"
readonly RESOLVED_DNS_CONFIG_PATH="/etc/systemd/resolved.conf.d/dns-optimization.conf"

setup_file() {
    skip_unless_docker_daemon_is_reachable
    build_privileged_test_image_or_fail "$DOCKER_IMAGE_TAG"
    skip_unless_privileged_container_can_write_kernel_network_settings "$DOCKER_IMAGE_TAG"
}

teardown_file() {
    remove_test_image_if_present "$DOCKER_IMAGE_TAG"
}

_run_in_privileged_container() {
    skip_unless_docker_daemon_is_reachable
    docker run --rm --privileged "$DOCKER_IMAGE_TAG" bash -c "$1"
}

@test "fresh install completes successfully" {
    run _run_in_privileged_container "$SCRIPT_PATH_INSIDE_CONTAINER"
    [ "$status" -eq 0 ]
    [[ "$output" == *"=== Done ==="* ]]
}

@test "sysctl config file written with all settings" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && cat $SYSCTL_NETWORK_CONFIG_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"net.core.rmem_max = 16777216"* ]]
    [[ "$output" == *"net.core.wmem_max = 16777216"* ]]
    [[ "$output" == *"net.ipv4.tcp_congestion_control = bbr"* ]]
    [[ "$output" == *"net.core.default_qdisc = fq"* ]]
    [[ "$output" == *"net.ipv4.tcp_fastopen = 3"* ]]
    [[ "$output" == *"net.ipv4.tcp_slow_start_after_idle = 0"* ]]
    [[ "$output" == *"net.ipv4.tcp_mtu_probing = 1"* ]]
    [[ "$output" == *"net.core.netdev_max_backlog = 16384"* ]]
}

@test "bbr congestion control applied live" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && sysctl -n net.ipv4.tcp_congestion_control"
    [ "$status" -eq 0 ]
    [[ "$output" == *"bbr"* ]]
}

@test "tcp fast open applied live" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && sysctl -n net.ipv4.tcp_fastopen"
    [ "$status" -eq 0 ]
    [[ "$output" == *"3"* ]]
}

@test "tcp slow start after idle disabled live" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && sysctl -n net.ipv4.tcp_slow_start_after_idle"
    [ "$status" -eq 0 ]
    [[ "$output" == *"0"* ]]
}

@test "wifi powersave config written" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && cat $NETWORKMANAGER_WIFI_POWERSAVE_CONFIG_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"wifi.powersave = 2"* ]]
}

@test "dns-over-tls config written" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && cat $RESOLVED_DNS_CONFIG_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"1.1.1.1#cloudflare-dns.com"* ]]
    [[ "$output" == *"DNSOverTLS=opportunistic"* ]]
}

@test "idempotent: second run succeeds" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && $SCRIPT_PATH_INSIDE_CONTAINER"
    [ "$status" -eq 0 ]
    [[ "$output" == *"=== Done ==="* ]]
}

@test "activation check passes after setup" {
    local activationCheckCondition='[ "$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null)" = "bbr" ] \
        && [ "$(sysctl -n net.ipv4.tcp_fastopen 2>/dev/null)" = "3" ] \
        && [ "$(sysctl -n net.ipv4.tcp_slow_start_after_idle 2>/dev/null)" = "0" ] \
        && [ "$(sysctl -n net.ipv4.tcp_mtu_probing 2>/dev/null)" = "1" ] \
        && grep -q "wifi.powersave = 2" /etc/NetworkManager/conf.d/wifi-powersave-off.conf 2>/dev/null \
        && grep -q "DNSOverTLS=opportunistic" /etc/systemd/resolved.conf.d/dns-optimization.conf 2>/dev/null'

    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && $activationCheckCondition && echo SKIP_CONFIRMED"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SKIP_CONFIRMED"* ]]
}
