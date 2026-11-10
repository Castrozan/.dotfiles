#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/docker-container-assertions'

readonly DOCKER_IMAGE_TAG="dotfiles-oom-test"
readonly SCRIPT_PATH_INSIDE_CONTAINER="/dotfiles/machine-configuration/operating-system/memory-protection/scripts/setup-oom-protection"
readonly EARLYOOM_CONFIG_PATH="/etc/default/earlyoom"
readonly ZRAMSWAP_CONFIG_PATH="/etc/default/zramswap"
readonly SWAPPINESS_SYSCTL_PATH="/etc/sysctl.d/99-swappiness.conf"
readonly ACTIVATION_CHECK_CONDITION='command -v earlyoom >/dev/null 2>&1 \
    && grep -q "ALGO=zstd" /etc/default/zramswap 2>/dev/null \
    && grep -q "PERCENT=50" /etc/default/zramswap 2>/dev/null \
    && [ "$(sysctl -n vm.swappiness 2>/dev/null)" = "150" ]'

setup_file() {
    skip_unless_docker_daemon_is_reachable
    build_privileged_test_image_or_fail "$DOCKER_IMAGE_TAG"
    docker run -d --rm --privileged "$DOCKER_IMAGE_TAG" sleep 1800 >"$BATS_FILE_TMPDIR/configured-container-id"
    local freshInstallStatus=0
    docker exec "$(_configured_container_id)" "$SCRIPT_PATH_INSIDE_CONTAINER" \
        >"$BATS_FILE_TMPDIR/fresh-install-output" 2>&1 || freshInstallStatus=$?
    echo "$freshInstallStatus" >"$BATS_FILE_TMPDIR/fresh-install-status"
}

teardown_file() {
    if docker_daemon_is_reachable && [[ -s "$BATS_FILE_TMPDIR/configured-container-id" ]]; then
        docker rm -f "$(_configured_container_id)" &>/dev/null || true
    fi
    remove_test_image_if_present "$DOCKER_IMAGE_TAG"
}

_configured_container_id() {
    cat "$BATS_FILE_TMPDIR/configured-container-id"
}

_run_in_configured_container() {
    docker exec "$(_configured_container_id)" bash -c "$1"
}

_run_in_fresh_privileged_container() {
    docker run --rm --privileged "$DOCKER_IMAGE_TAG" bash -c "$1"
}

@test "fresh install completes successfully" {
    [ "$(cat "$BATS_FILE_TMPDIR/fresh-install-status")" -eq 0 ]
    [[ "$(cat "$BATS_FILE_TMPDIR/fresh-install-output")" == *"=== Done ==="* ]]
}

@test "earlyoom and zram-tools installed after fresh run" {
    run _run_in_configured_container "dpkg -l earlyoom && dpkg -l zram-tools"
    [ "$status" -eq 0 ]
}

@test "earlyoom config written correctly" {
    run _run_in_configured_container "cat $EARLYOOM_CONFIG_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"-m 10"* ]]
    [[ "$output" == *"-s 15"* ]]
}

@test "zramswap config written correctly" {
    run _run_in_configured_container "cat $ZRAMSWAP_CONFIG_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"ALGO=zstd"* ]]
    [[ "$output" == *"PERCENT=50"* ]]
    [[ "$output" == *"PRIORITY=100"* ]]
}

@test "swappiness persisted to sysctl.d" {
    run _run_in_configured_container "cat $SWAPPINESS_SYSCTL_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"vm.swappiness=150"* ]]
}

@test "idempotent: second run succeeds" {
    run _run_in_configured_container "$SCRIPT_PATH_INSIDE_CONTAINER"
    [ "$status" -eq 0 ]
    [[ "$output" == *"=== Done ==="* ]]
}

@test "activation skips when already configured" {
    run _run_in_configured_container "$ACTIVATION_CHECK_CONDITION && echo SKIP_CONFIRMED"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SKIP_CONFIRMED"* ]]
}

@test "activation detects partial config" {
    run _run_in_fresh_privileged_container \
        "apt-get update -qq && apt-get install -y -qq earlyoom && ! ($ACTIVATION_CHECK_CONDITION) && echo PARTIAL_DETECTED"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PARTIAL_DETECTED"* ]]
}
