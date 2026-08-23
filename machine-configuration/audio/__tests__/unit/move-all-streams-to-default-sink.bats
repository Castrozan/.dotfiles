#!/usr/bin/env bats

load '../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	FAKE_BIN_DIRECTORY="$BATS_TEST_TMPDIR/bin"
	mkdir -p "$FAKE_BIN_DIRECTORY"

	export PACTL_CALL_LOG="$BATS_TEST_TMPDIR/pactl-calls.log"
	export PACTL_SINK_TABLE="$BATS_TEST_TMPDIR/sinks.txt"
	export PACTL_SINK_INPUT_TABLE="$BATS_TEST_TMPDIR/sink-inputs.txt"
	export PACTL_DEFAULT_SINK_NAME="bluez_output.AA_BB_CC.1"
	: >"$PACTL_SINK_TABLE"
	: >"$PACTL_SINK_INPUT_TABLE"

	cat >"$FAKE_BIN_DIRECTORY/pactl" <<-'FAKE_PACTL'
		#!/usr/bin/env bash
		echo "$*" >>"$PACTL_CALL_LOG"
		case "$1 $2" in
			"get-default-sink ") echo "$PACTL_DEFAULT_SINK_NAME" ;;
			"list sinks") cat "$PACTL_SINK_TABLE" ;;
			"list sink-inputs") cat "$PACTL_SINK_INPUT_TABLE" ;;
		esac
		exit 0
	FAKE_PACTL

	chmod +x "$FAKE_BIN_DIRECTORY/pactl"
	PATH="$FAKE_BIN_DIRECTORY:$PATH"
}

announce_sink() {
	echo "$1	$2	module-bluez5-device.c	s16le 2ch 48000Hz	RUNNING" >>"$PACTL_SINK_TABLE"
}

announce_stream() {
	echo "$1	14	4	s16le 2ch 48000Hz	RUNNING" >>"$PACTL_SINK_INPUT_TABLE"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "moves every playing stream onto the default sink index" {
	announce_sink 7 alsa_output.pci-0000_00_1f.3.analog-stereo
	announce_sink 42 "$PACTL_DEFAULT_SINK_NAME"
	announce_stream 100
	announce_stream 101

	run_script_under_test

	grep -qxF "move-sink-input 100 42" "$PACTL_CALL_LOG"
	grep -qxF "move-sink-input 101 42" "$PACTL_CALL_LOG"
}

@test "moves nothing when the default sink is missing from the sink table" {
	announce_sink 7 alsa_output.pci-0000_00_1f.3.analog-stereo
	announce_stream 100

	run_script_under_test

	run grep -c "move-sink-input" "$PACTL_CALL_LOG"
	[ "$output" = "0" ]
}
