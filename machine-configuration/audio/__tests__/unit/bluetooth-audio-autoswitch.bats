#!/usr/bin/env bats

load '../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	FAKE_BIN_DIRECTORY="$BATS_TEST_TMPDIR/bin"
	mkdir -p "$FAKE_BIN_DIRECTORY"

	export PACTL_CALL_LOG="$BATS_TEST_TMPDIR/pactl-calls.log"
	export PACTL_EVENT_STREAM="$BATS_TEST_TMPDIR/events.txt"
	export PACTL_SINK_TABLE="$BATS_TEST_TMPDIR/sinks.txt"
	export MOVE_STREAMS_CALL_LOG="$BATS_TEST_TMPDIR/move-streams.log"
	export SLEEP_CALL_LOG="$BATS_TEST_TMPDIR/sleep.log"
	: >"$PACTL_EVENT_STREAM"
	: >"$PACTL_SINK_TABLE"

	cat >"$FAKE_BIN_DIRECTORY/pactl" <<-'FAKE_PACTL'
		#!/usr/bin/env bash
		echo "$*" >>"$PACTL_CALL_LOG"
		case "$1" in
			subscribe) cat "$PACTL_EVENT_STREAM" ;;
			list) if [ "$2" = "sinks" ]; then cat "$PACTL_SINK_TABLE"; fi ;;
		esac
		exit 0
	FAKE_PACTL

	cat >"$FAKE_BIN_DIRECTORY/move-all-streams-to-default-sink" <<-'FAKE_MOVER'
		#!/usr/bin/env bash
		echo moved >>"$MOVE_STREAMS_CALL_LOG"
	FAKE_MOVER

	cat >"$FAKE_BIN_DIRECTORY/sleep" <<-'FAKE_SLEEP'
		#!/usr/bin/env bash
		echo "$*" >>"$SLEEP_CALL_LOG"
	FAKE_SLEEP

	chmod +x "$FAKE_BIN_DIRECTORY"/*
	PATH="$FAKE_BIN_DIRECTORY:$PATH"
}

require_perl_compatible_grep() {
	if ! echo "x#7" | grep -oP '#\K\d+' >/dev/null 2>&1; then
		skip "needs GNU grep -P; the bluetooth listener is a Linux-only capability"
	fi
}

announce_sink() {
	echo "$1	$2	module-bluez5-device.c	s16le 2ch 48000Hz	RUNNING" >>"$PACTL_SINK_TABLE"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "makes a newly appeared bluetooth sink the default and moves streams onto it" {
	require_perl_compatible_grep
	announce_sink 42 bluez_output.AA_BB_CC.1
	echo "Event 'new' on sink #42" >"$PACTL_EVENT_STREAM"

	run_script_under_test

	grep -qxF "set-default-sink bluez_output.AA_BB_CC.1" "$PACTL_CALL_LOG"
	grep -qxF "0.5" "$SLEEP_CALL_LOG"
	grep -qxF "moved" "$MOVE_STREAMS_CALL_LOG"
}

@test "leaves a newly appeared non-bluetooth sink alone" {
	require_perl_compatible_grep
	announce_sink 7 alsa_output.pci-0000_00_1f.3.analog-stereo
	echo "Event 'new' on sink #7" >"$PACTL_EVENT_STREAM"

	run_script_under_test

	run grep -c "set-default-sink" "$PACTL_CALL_LOG"
	[ "$output" = "0" ]
	[ ! -f "$MOVE_STREAMS_CALL_LOG" ]
}

@test "moves streams back after a sink is removed" {
	echo "Event 'remove' on sink #42" >"$PACTL_EVENT_STREAM"

	run_script_under_test

	grep -qxF "0.5" "$SLEEP_CALL_LOG"
	grep -qxF "moved" "$MOVE_STREAMS_CALL_LOG"
	run grep -c "set-default-sink" "$PACTL_CALL_LOG"
	[ "$output" = "0" ]
}
