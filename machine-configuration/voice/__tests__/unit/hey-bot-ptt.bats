#!/usr/bin/env bats

load '../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/hey-bot-ptt"
	export SCRIPT_UNDER_TEST
	REAL_MKTEMP="$(command -v mktemp)"
	export REAL_MKTEMP
	unset BASH_ENV

	export HOME="$BATS_TEST_TMPDIR/home"
	mkdir -p "$HOME"

	export HEY_BOT_GATEWAY_URL="http://gateway.invalid"
	export HEY_BOT_GATEWAY_TOKEN_FILE="$BATS_TEST_TMPDIR/gateway-token"
	export HEY_BOT_AGENT_ID="main"
	export HEY_BOT_TTS_VOICE="en-US-JennyNeural"
	export HEY_BOT_MODEL="test-model"
	printf 'gateway-token' >"$HEY_BOT_GATEWAY_TOKEN_FILE"

	export RECORDER_CALL_LOG="$BATS_TEST_TMPDIR/recorder-calls.log"
	export CLIPBOARD_FILE="$BATS_TEST_TMPDIR/clipboard.txt"
	export NOTIFY_CALL_LOG="$BATS_TEST_TMPDIR/notify-calls.log"
	export GATEWAY_REQUEST_LOG="$BATS_TEST_TMPDIR/gateway-requests.log"
	export GATEWAY_RESPONSE_FILE="$BATS_TEST_TMPDIR/gateway-response.json"
	export TTS_CALL_LOG="$BATS_TEST_TMPDIR/tts-calls.log"
	export TTS_EXIT_CODE=0
	export PLAYER_CALL_LOG="$BATS_TEST_TMPDIR/player-calls.log"
	export SINK_CALL_LOG="$BATS_TEST_TMPDIR/sink-calls.log"
	export MKTEMP_PATH_LOG="$BATS_TEST_TMPDIR/mktemp-paths.log"
	: >"$CLIPBOARD_FILE"
	printf '{"choices":[{"message":{"content":"The weather is fine."}}]}' >"$GATEWAY_RESPONSE_FILE"

	FAKE_BIN_DIRECTORY="$BATS_TEST_TMPDIR/bin"
	mkdir -p "$FAKE_BIN_DIRECTORY"

	cat >"$FAKE_BIN_DIRECTORY/whisp-away" <<-'FAKE_RECORDER'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$RECORDER_CALL_LOG"
	FAKE_RECORDER

	cat >"$FAKE_BIN_DIRECTORY/wl-paste" <<-'FAKE_CLIPBOARD'
		#!/usr/bin/env bash
		cat "$CLIPBOARD_FILE"
	FAKE_CLIPBOARD

	cat >"$FAKE_BIN_DIRECTORY/notify-send" <<-'FAKE_NOTIFY'
		#!/usr/bin/env bash
		printf '%s|%s\n' "$1" "$2" >>"$NOTIFY_CALL_LOG"
	FAKE_NOTIFY

	cat >"$FAKE_BIN_DIRECTORY/curl" <<-'FAKE_CURL'
		#!/usr/bin/env bash
		requestBody=""
		while [ $# -gt 0 ]; do
			if [ "$1" = "-d" ]; then requestBody="$2"; shift; fi
			shift
		done
		printf '%s\n' "$requestBody" >>"$GATEWAY_REQUEST_LOG"
		cat "$GATEWAY_RESPONSE_FILE"
	FAKE_CURL

	cat >"$FAKE_BIN_DIRECTORY/edge-tts" <<-'FAKE_TTS'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$TTS_CALL_LOG"
		mediaPath=""
		while [ $# -gt 0 ]; do
			if [ "$1" = "--write-media" ]; then mediaPath="$2"; shift; fi
			shift
		done
		if [ -n "$mediaPath" ]; then : >"$mediaPath"; fi
		exit "$TTS_EXIT_CODE"
	FAKE_TTS

	cat >"$FAKE_BIN_DIRECTORY/mpv" <<-'FAKE_PLAYER'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$PLAYER_CALL_LOG"
	FAKE_PLAYER

	cat >"$FAKE_BIN_DIRECTORY/wpctl" <<-'FAKE_SINK'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$SINK_CALL_LOG"
	FAKE_SINK

	cat >"$FAKE_BIN_DIRECTORY/mktemp" <<-'FAKE_MKTEMP'
		#!/usr/bin/env bash
		if "$REAL_MKTEMP" --version >/dev/null 2>&1; then
			createdPath="$("$REAL_MKTEMP" "$@")"
		else
			namePrefix="${1%%XXXXXX*}"
			nameSuffix="${1##*XXXXXX}"
			while :; do
				createdPath="$namePrefix$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')$nameSuffix"
				[ -e "$createdPath" ] || break
			done
			: >"$createdPath"
		fi
		printf '%s\n' "$createdPath" >>"$MKTEMP_PATH_LOG"
		printf '%s\n' "$createdPath"
	FAKE_MKTEMP

	chmod +x "$FAKE_BIN_DIRECTORY"/*
	PATH="$FAKE_BIN_DIRECTORY:$PATH"
}

teardown() {
	if [ -f "$MKTEMP_PATH_LOG" ]; then
		while read -r temporaryPath; do rm -f "$temporaryPath"; done <"$MKTEMP_PATH_LOG"
	fi
}

speak() {
	printf '%s' "$1" >"$CLIPBOARD_FILE"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "stops the recorder into the clipboard before reading it" {
	speak "what is the weather"
	run_script_under_test
	[ "$status" -eq 0 ]
	grep -qxF "stop --clipboard true" "$RECORDER_CALL_LOG"
}

@test "reports no speech and stops before the gateway when the clipboard is empty" {
	run_script_under_test
	[ "$status" -eq 0 ]
	grep -qxF "Hey Bot|No speech detected" "$NOTIFY_CALL_LOG"
	[ ! -f "$GATEWAY_REQUEST_LOG" ]
	[ ! -f "$TTS_CALL_LOG" ]
}

@test "notifies with the transcription and sends it to the gateway" {
	speak "what is the weather"
	run_script_under_test
	[ "$status" -eq 0 ]
	grep -qxF "Hey Bot|what is the weather" "$NOTIFY_CALL_LOG"

	run jq -r '.messages[0].content' "$GATEWAY_REQUEST_LOG"
	[[ "$output" == *"[Voice input — respond concisely for TTS playback."* ]]
	[[ "$output" == *"what is the weather"* ]]
	run jq -r '.model' "$GATEWAY_REQUEST_LOG"
	[ "$output" = "test-model" ]
	run jq -r '.user' "$GATEWAY_REQUEST_LOG"
	[ "$output" = "voice-main" ]
}

@test "speaks the reply through the player after unmuting the sink" {
	speak "what is the weather"
	run_script_under_test
	[ "$status" -eq 0 ]
	grep -qF "The weather is fine." "$TTS_CALL_LOG"
	grep -qF "en-US-JennyNeural" "$TTS_CALL_LOG"
	grep -qxF "set-mute @DEFAULT_AUDIO_SINK@ 0" "$SINK_CALL_LOG"
	grep -qF -- "--no-video --ao=pulse" "$PLAYER_CALL_LOG"
}

@test "an unparsable gateway reply speaks the processing failure" {
	printf '{"error":"upstream exploded"}' >"$GATEWAY_RESPONSE_FILE"
	speak "what is the weather"
	run_script_under_test
	[ "$status" -eq 0 ]
	grep -qF "Sorry, I could not process that." "$TTS_CALL_LOG"
}

@test "a text to speech failure skips playback" {
	export TTS_EXIT_CODE=1
	speak "what is the weather"
	run_script_under_test
	[ "$status" -eq 0 ]
	[ -f "$TTS_CALL_LOG" ]
	[ ! -f "$PLAYER_CALL_LOG" ]
	[ ! -f "$SINK_CALL_LOG" ]
}

@test "removes the rendered audio file when it exits" {
	speak "what is the weather"
	run_script_under_test
	[ "$status" -eq 0 ]

	local renderedAudioFile
	renderedAudioFile="$(cat "$MKTEMP_PATH_LOG")"
	[[ "$renderedAudioFile" == /tmp/hey-bot-ptt-*.mp3 ]]
	[ ! -e "$renderedAudioFile" ]
}
