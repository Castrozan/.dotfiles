#!/usr/bin/env bats

load '../../../../../__tests__/helpers/docker-container-assertions'

readonly DOCKER_IMAGE_TAG="dotfiles-oom-test"
readonly SCRIPT_PATH_INSIDE_CONTAINER="/dotfiles/home/base/system/scripts/setup-oom-protection"
readonly EARLYOOM_CONFIG_PATH="/etc/default/earlyoom"
readonly ZRAMSWAP_CONFIG_PATH="/etc/default/zramswap"
readonly SWAPPINESS_SYSCTL_PATH="/etc/sysctl.d/99-swappiness.conf"

setup_file() {
    skip_unless_docker_daemon_is_reachable
    build_privileged_test_image_or_fail "$DOCKER_IMAGE_TAG"
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

@test "earlyoom and zram-tools installed after fresh run" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && dpkg -l earlyoom && dpkg -l zram-tools"
    [ "$status" -eq 0 ]
}

@test "earlyoom config written correctly" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && cat $EARLYOOM_CONFIG_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"-m 10"* ]]
    [[ "$output" == *"-s 15"* ]]
}

@test "zramswap config written correctly" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && cat $ZRAMSWAP_CONFIG_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"ALGO=zstd"* ]]
    [[ "$output" == *"PERCENT=50"* ]]
    [[ "$output" == *"PRIORITY=100"* ]]
}

@test "swappiness persisted to sysctl.d" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && cat $SWAPPINESS_SYSCTL_PATH"
    [ "$status" -eq 0 ]
    [[ "$output" == *"vm.swappiness=150"* ]]
}

@test "idempotent: second run succeeds" {
    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && $SCRIPT_PATH_INSIDE_CONTAINER"
    [ "$status" -eq 0 ]
    [[ "$output" == *"=== Done ==="* ]]
}

@test "activation skips when already configured" {
    local activationCheckCondition='command -v earlyoom >/dev/null 2>&1 \
        && grep -q "ALGO=zstd" /etc/default/zramswap 2>/dev/null \
        && grep -q "PERCENT=50" /etc/default/zramswap 2>/dev/null \
        && [ "$(sysctl -n vm.swappiness 2>/dev/null)" = "150" ]'

    run _run_in_privileged_container \
        "$SCRIPT_PATH_INSIDE_CONTAINER && $activationCheckCondition && echo SKIP_CONFIRMED"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SKIP_CONFIRMED"* ]]
}

@test "activation detects partial config" {
    local activationCheckCondition='command -v earlyoom >/dev/null 2>&1 \
        && grep -q "ALGO=zstd" /etc/default/zramswap 2>/dev/null \
        && grep -q "PERCENT=50" /etc/default/zramswap 2>/dev/null \
        && [ "$(sysctl -n vm.swappiness 2>/dev/null)" = "150" ]'

    run _run_in_privileged_container \
        "apt-get update -qq && apt-get install -y -qq earlyoom && ! ($activationCheckCondition) && echo PARTIAL_DETECTED"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PARTIAL_DETECTED"* ]]
}
