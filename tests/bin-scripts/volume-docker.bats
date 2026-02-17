#!/usr/bin/env bats

readonly DOCKER_IMAGE_TAG="dotfiles-volume-test"
readonly VOLUME_SCRIPT="/dotfiles/bin/volume"
readonly MOCK_SETUP='
    cp /dotfiles/tests/helpers/mock-pactl /usr/local/bin/pactl
    cp /dotfiles/tests/helpers/mock-notify-send /usr/local/bin/notify-send
    chmod +x /usr/local/bin/pactl /usr/local/bin/notify-send
    export MOCK_PACTL_STATE_DIR=/tmp/mock-pactl
    export MOCK_NOTIFY_SEND_LOG=/tmp/mock-notify-send.log
    mkdir -p /tmp/mock-pactl
    mkdir -p "$HOME/.config/scripts/icons"
    touch "$HOME/.config/scripts/icons/volume-mute.png"
    touch "$HOME/.config/scripts/icons/volume-low.png"
    touch "$HOME/.config/scripts/icons/volume-mid.png"
    touch "$HOME/.config/scripts/icons/volume-high.png"
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

_run_volume_in_container() {
    if ! command -v docker &>/dev/null; then
        skip "docker not in PATH"
    fi
    docker run --rm "$DOCKER_IMAGE_TAG" bash -c "$MOCK_SETUP $1"
}

@test "get volume returns numeric value" {
    run _run_volume_in_container "$VOLUME_SCRIPT --get"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^[0-9]+$ ]]
}

@test "get volume icon returns valid path" {
    run _run_volume_in_container "$VOLUME_SCRIPT --get-icon"
    [ "$status" -eq 0 ]
    [[ "$output" == *"volume-"* ]]
    [[ "$output" == *".png" ]]
}

@test "increase volume by normal step" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --inc
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "55" ]]
}

@test "decrease volume by normal step" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --dec
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "45" ]]
}

@test "increase volume by precise step" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --inc-precise
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "51" ]]
}

@test "decrease volume by precise step" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --dec-precise
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "49" ]]
}

@test "toggle mute sends notification" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --toggle
        cat /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"Volume Muted"* ]]
}

@test "toggle mute twice restores unmuted state" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --toggle
        $VOLUME_SCRIPT --toggle
        cat /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"Volume: 50%"* ]]
}

@test "toggle mic mute sends notification" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --toggle-mic
        cat /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"Microphone Muted"* ]]
}

@test "mic increase changes source volume" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --mic-inc
        cat /tmp/mock-pactl/source-alsa_input.mock.analog-stereo
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"volume=55"* ]]
}

@test "mic decrease changes source volume" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --mic-dec
        cat /tmp/mock-pactl/source-alsa_input.mock.analog-stereo
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"volume=45"* ]]
}

@test "targets running sink when available" {
    run _run_volume_in_container "
        echo '38	echo-cancel-sink	PipeWire	float32le 1ch 48000Hz	IDLE' > /tmp/mock-pactl/sinks-short
        echo '55	alsa_output.hardware.analog-stereo	PipeWire	s32le 2ch 48000Hz	RUNNING' >> /tmp/mock-pactl/sinks-short
        echo 'echo-cancel-sink' > /tmp/mock-pactl/default-sink
        echo 'volume=30 mute=no' > /tmp/mock-pactl/sink-echo-cancel-sink
        echo 'volume=70 mute=no' > /tmp/mock-pactl/sink-alsa_output.hardware.analog-stereo

        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "70" ]]
}

@test "falls back to default sink when none running" {
    run _run_volume_in_container "
        echo '38	echo-cancel-sink	PipeWire	float32le 1ch 48000Hz	IDLE' > /tmp/mock-pactl/sinks-short
        echo '55	alsa_output.hardware.analog-stereo	PipeWire	s32le 2ch 48000Hz	IDLE' >> /tmp/mock-pactl/sinks-short
        echo 'alsa_output.hardware.analog-stereo' > /tmp/mock-pactl/default-sink
        echo 'volume=30 mute=no' > /tmp/mock-pactl/sink-echo-cancel-sink
        echo 'volume=42 mute=no' > /tmp/mock-pactl/sink-alsa_output.hardware.analog-stereo

        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "volume notifications include progress bar value" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --inc
        cat /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"int:value:55"* ]]
}

@test "notifications use synchronous tag for stacking" {
    run _run_volume_in_container "
        $VOLUME_SCRIPT --inc
        cat /tmp/mock-notify-send.log
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"x-canonical-private-synchronous:volume"* ]]
}

@test "volume does not go below zero" {
    run _run_volume_in_container "
        echo 'volume=2 mute=no' > /tmp/mock-pactl/sink-alsa_output.mock.analog-stereo
        $VOLUME_SCRIPT --dec
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "0" ]]
}

@test "stress: 50 rapid volume increases complete without error" {
    run _run_volume_in_container "
        for i in \$(seq 1 50); do
            $VOLUME_SCRIPT --inc-precise
        done
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "100" ]]
}

@test "stress: 100 rapid inc/dec cycles complete without error" {
    run _run_volume_in_container "
        for i in \$(seq 1 100); do
            $VOLUME_SCRIPT --inc-precise
            $VOLUME_SCRIPT --dec-precise
        done
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "50" ]]
}

@test "stress: 50 rapid mute toggles complete without error" {
    run _run_volume_in_container "
        for i in \$(seq 1 50); do
            $VOLUME_SCRIPT --toggle
        done
        $VOLUME_SCRIPT --get
    "
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^[0-9]+$ ]]
}

@test "stress: interleaved volume and mic operations" {
    run _run_volume_in_container "
        for i in \$(seq 1 25); do
            $VOLUME_SCRIPT --inc
            $VOLUME_SCRIPT --mic-inc
            $VOLUME_SCRIPT --dec-precise
            $VOLUME_SCRIPT --mic-dec
        done
        echo COMPLETE
    "
    [ "$status" -eq 0 ]
    [[ "$output" == *"COMPLETE"* ]]
}
