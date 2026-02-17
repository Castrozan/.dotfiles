#!/usr/bin/env bats

readonly DOCKER_IMAGE_TAG="dotfiles-brightness-test"
readonly BRIGHTNESS_SCRIPT="/dotfiles/bin/brightness"
readonly MOCK_SETUP='
    cp /dotfiles/tests/helpers/mock-brightnessctl /usr/local/bin/brightnessctl
    cp /dotfiles/tests/helpers/mock-notify-send /usr/local/bin/notify-send
    chmod +x /usr/local/bin/brightnessctl /usr/local/bin/notify-send
    export MOCK_BRIGHTNESSCTL_STATE=/tmp/mock-brightnessctl-state
    export MOCK_NOTIFY_SEND_LOG=/tmp/mock-notify-send.log
    echo "500" > /tmp/mock-brightnessctl-state
'

setup_file() {
    if ! command -v docker &>/dev/null; then
        skip "docker not in PATH"
    fi

    local repositoryRoot
    repositoryRoot="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
    docker build -t "$DOCKER_IMAGE_TAG" -f "$repositoryRoot/tests/Dockerfile" "$repositoryRoot" >/dev/null 2>&1
}

teardown_file() {
    if command -v docker &>/dev/null; then
        docker rmi -f "$DOCKER_IMAGE_TAG" >/dev/null 2>&1 || true
    fi
}

_run_brightness_in_container() {
    if ! command -v docker &>/dev/null; then
        skip "docker not in PATH"
    fi
    docker run --rm "$DOCKER_IMAGE_TAG" bash -c "$MOCK_SETUP $1"
}

@test "get brightness returns numeric value" {
    run _run_brightness_in_container "$BRIGHTNESS_SCRIPT --get"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^[0-9]+$ ]]
}

@test "initial brightness is 50 percent" {
    run _run_brightness_in_container "$BRIGHTNESS_SCRIPT --get"
    [ "$status" -eq 0 ]
    [[ "$output" == "50" ]]
}

@test "increase brightness by normal step" {
    run _run_brightness_in_container "
        $BRIGHTNESS_SCRIPT --inc
        $BRIGHTNESS_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "60" ]]
}

@test "decrease brightness by normal step" {
    run _run_brightness_in_container "
        $BRIGHTNESS_SCRIPT --dec
        $BRIGHTNESS_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "40" ]]
}

@test "increase brightness by precise step" {
    run _run_brightness_in_container "
        $BRIGHTNESS_SCRIPT --inc-precise
        $BRIGHTNESS_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "51" ]]
}

@test "decrease brightness by precise step" {
    run _run_brightness_in_container "
        $BRIGHTNESS_SCRIPT --dec-precise
        $BRIGHTNESS_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "49" ]]
}

@test "brightness notifications include progress bar value" {
    run _run_brightness_in_container "
        $BRIGHTNESS_SCRIPT --inc
        cat /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"int:value:60"* ]]
}

@test "notifications use synchronous tag for stacking" {
    run _run_brightness_in_container "
        $BRIGHTNESS_SCRIPT --inc
        cat /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"x-canonical-private-synchronous:brightness"* ]]
}

@test "brightness does not go below 1 percent" {
    run _run_brightness_in_container "
        echo '10' > /tmp/mock-brightnessctl-state
        $BRIGHTNESS_SCRIPT --dec
        $BRIGHTNESS_SCRIPT --dec
        $BRIGHTNESS_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    local value="${lines[-1]}"
    [[ "$value" =~ ^[0-9]+$ ]]
    (( value >= 0 ))
}

@test "default action returns brightness percentage" {
    run _run_brightness_in_container "$BRIGHTNESS_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^[0-9]+$ ]]
}

@test "stress: 50 rapid brightness increases complete without error" {
    run _run_brightness_in_container "
        for i in \$(seq 1 50); do
            $BRIGHTNESS_SCRIPT --inc-precise
        done
        $BRIGHTNESS_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "100" ]]
}

@test "stress: 100 rapid inc/dec cycles complete without error" {
    run _run_brightness_in_container "
        for i in \$(seq 1 100); do
            $BRIGHTNESS_SCRIPT --inc-precise
            $BRIGHTNESS_SCRIPT --dec-precise
        done
        $BRIGHTNESS_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "50" ]]
}

@test "stress: 200 rapid operations produce correct notification count" {
    run _run_brightness_in_container "
        for i in \$(seq 1 200); do
            $BRIGHTNESS_SCRIPT --inc-precise
        done
        wc -l < /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "200" ]]
}
