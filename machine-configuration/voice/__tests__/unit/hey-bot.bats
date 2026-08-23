#!/usr/bin/env bats

load '../../../../repository/verification/helpers/bash-script-assertions'

readonly KEYWORDS_DISABLED_FLAG_FILE="/tmp/hey-bot-keywords-disabled"

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/hey-bot"
	export SCRIPT_UNDER_TEST
	REAL_MKTEMP="$(command -v mktemp)"
	export REAL_MKTEMP
	unset BASH_ENV

	export HOME="$BATS_TEST_TMPDIR/home"
	mkdir -p "$HOME"

	export HEY_BOT_WHISPER_MODEL="$BATS_TEST_TMPDIR/ggml-base.bin"
	export HEY_BOT_KEYWORDS_PATTERN="clever|jarvis"
	export HEY_BOT_GATEWAY_URL="http://gateway.invalid"
	export HEY_BOT_GATEWAY_TOKEN_FILE="$BATS_TEST_TMPDIR/gateway-token"
	export HEY_BOT_AGENT_ID="main"
	export HEY_BOT_TTS_VOICE="en-US-JennyNeural"
	export HEY_BOT_MODEL="test-model"
	export HEY_BOT_TRANSCRIPTION_DIR="$HOME/.local/share/hey-bot/transcriptions"
	export HEY_BOT_MAX_LOG_SIZE=1048576
	printf 'gateway-token' >"$HEY_BOT_GATEWAY_TOKEN_FILE"
	mkdir -p "$HEY_BOT_TRANSCRIPTION_DIR"

	CURRENT_LOG_FILE="$HEY_BOT_TRANSCRIPTION_DIR/current.log"
	DAEMON_OUTPUT="$BATS_TEST_TMPDIR/daemon-output.txt"
	: >"$DAEMON_OUTPUT"

	export DAEMON_SHUTDOWN_MARKER="$BATS_TEST_TMPDIR/daemon-shutdown"
	export TRANSCRIPT_QUEUE="$BATS_TEST_TMPDIR/transcripts.txt"
	export WHISPER_CALL_LOG="$BATS_TEST_TMPDIR/whisper-calls.log"
	export AMPLITUDE_VALUE="0.500000"
	export RECORDED_CHUNK_LOG="$BATS_TEST_TMPDIR/recorded-chunks.log"
	export MKTEMP_PATH_LOG="$BATS_TEST_TMPDIR/mktemp-paths.log"
	export NOTIFY_CALL_LOG="$BATS_TEST_TMPDIR/notify-calls.log"
	export GATEWAY_REQUEST_LOG="$BATS_TEST_TMPDIR/gateway-requests.log"
	export GATEWAY_RESPONSE_FILE="$BATS_TEST_TMPDIR/gateway-response.json"
	export TTS_CALL_LOG="$BATS_TEST_TMPDIR/tts-calls.log"
	export TTS_EXIT_CODE=0
	export PLAYER_CALL_LOG="$BATS_TEST_TMPDIR/player-calls.log"
	export SINK_CALL_LOG="$BATS_TEST_TMPDIR/sink-calls.log"
	: >"$TRANSCRIPT_QUEUE"
	respond_with_content "Everything is fine."

	FAKE_BIN_DIRECTORY="$BATS_TEST_TMPDIR/bin"
	mkdir -p "$FAKE_BIN_DIRECTORY"

	cat >"$FAKE_BIN_DIRECTORY/rec" <<-'FAKE_RECORDER'
		#!/usr/bin/env bash
		printf '%s\n' "$2" >>"$RECORDED_CHUNK_LOG"
		: >"$2"
	FAKE_RECORDER

	cat >"$FAKE_BIN_DIRECTORY/sox" <<-'FAKE_SOX'
		#!/usr/bin/env bash
		echo "Maximum amplitude:     $AMPLITUDE_VALUE"
	FAKE_SOX

	cat >"$FAKE_BIN_DIRECTORY/whisper-cli" <<-'FAKE_WHISPER'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$WHISPER_CALL_LOG"
		waitedTicks=0
		while [ ! -s "$TRANSCRIPT_QUEUE" ]; do
			if [ -e "$DAEMON_SHUTDOWN_MARKER" ] || [ "$waitedTicks" -ge 1500 ]; then exit 0; fi
			waitedTicks=$((waitedTicks + 1))
			/bin/sleep 0.02
		done
		head -1 "$TRANSCRIPT_QUEUE"
		tail -n +2 "$TRANSCRIPT_QUEUE" >"$TRANSCRIPT_QUEUE.remaining"
		mv "$TRANSCRIPT_QUEUE.remaining" "$TRANSCRIPT_QUEUE"
	FAKE_WHISPER

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

	cat >"$FAKE_BIN_DIRECTORY/sleep" <<-'FAKE_SLEEP'
		#!/usr/bin/env bash
		exec /bin/sleep 0.02
	FAKE_SLEEP

	cat >"$FAKE_BIN_DIRECTORY/stat" <<-'FAKE_STAT'
		#!/usr/bin/env bash
		if [ "$1" = "-c%s" ]; then
			wc -c <"$2" | tr -d ' '
			exit 0
		fi
		exec /usr/bin/stat "$@"
	FAKE_STAT

	cat >"$FAKE_BIN_DIRECTORY/mktemp" <<-'FAKE_MKTEMP'
		#!/usr/bin/env bash
		if "$REAL_MKTEMP" --version >/dev/null 2>&1; then
			createdPath="$("$REAL_MKTEMP" "$@")"
		else
			if [ "$1" = "-d" ]; then makeDirectory=1; shift; else makeDirectory=0; fi
			namePrefix="${1%%XXXXXX*}"
			nameSuffix="${1##*XXXXXX}"
			while :; do
				createdPath="$namePrefix$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')$nameSuffix"
				[ -e "$createdPath" ] || break
			done
			if [ "$makeDirectory" -eq 1 ]; then mkdir "$createdPath"; else : >"$createdPath"; fi
		fi
		printf '%s\n' "$createdPath" >>"$MKTEMP_PATH_LOG"
		printf '%s\n' "$createdPath"
	FAKE_MKTEMP

	chmod +x "$FAKE_BIN_DIRECTORY"/*
	PATH="$FAKE_BIN_DIRECTORY:$PATH"
}

teardown() {
	stop_daemon
	if [ -f "$MKTEMP_PATH_LOG" ]; then
		while read -r temporaryPath; do rm -f "$temporaryPath"; done <"$MKTEMP_PATH_LOG"
	fi
	if [ -n "${DAEMON_PID:-}" ]; then
		rm -f "/tmp/hey-bot-followup-$DAEMON_PID" "/tmp/hey-bot-wait-context-$DAEMON_PID"
	fi
	if [ -n "${KEYWORDS_DISABLED_FLAG_OWNED:-}" ]; then
		rm -f "$KEYWORDS_DISABLED_FLAG_FILE"
	fi
}

start_daemon() {
	"$SCRIPT_UNDER_TEST" >"$DAEMON_OUTPUT" 2>&1 &
	DAEMON_PID=$!
}

stop_daemon() {
	if [ -n "${DAEMON_PID:-}" ]; then
		touch "$DAEMON_SHUTDOWN_MARKER"
		pkill -P "$DAEMON_PID" 2>/dev/null || true
		kill "$DAEMON_PID" 2>/dev/null || true
		wait "$DAEMON_PID" 2>/dev/null || true
		/bin/sleep 0.1
		DAEMON_PID=""
	fi
}

queue_transcriptions() {
	printf '%s\n' "$@" >>"$TRANSCRIPT_QUEUE"
}

respond_with_content() {
	printf '{"choices":[{"message":{"content":%s}}]}' "$(printf '%s' "$1" | jq -Rs .)" >"$GATEWAY_RESPONSE_FILE"
}

wait_for_output() {
	local expectedText="$1"
	local attempt
	for attempt in $(seq 1 400); do
		if grep -qF -- "$expectedText" "$DAEMON_OUTPUT" 2>/dev/null; then
			return 0
		fi
		/bin/sleep 0.02
	done
	echo "timed out waiting for: $expectedText" >&2
	cat "$DAEMON_OUTPUT" >&2
	return 1
}

wait_for_file() {
	local expectedPath="$1"
	local attempt
	for attempt in $(seq 1 400); do
		if [ -e "$expectedPath" ]; then
			return 0
		fi
		/bin/sleep 0.02
	done
	echo "timed out waiting for file: $expectedPath" >&2
	return 1
}

wait_for_followup_signal() {
	wait_for_file "/tmp/hey-bot-followup-$DAEMON_PID"
}

wait_for_recorded_chunks() {
	local expectedCount="$1"
	local attempt
	for attempt in $(seq 1 400); do
		if [ -f "$RECORDED_CHUNK_LOG" ] && [ "$(wc -l <"$RECORDED_CHUNK_LOG")" -ge "$expectedCount" ]; then
			return 0
		fi
		/bin/sleep 0.02
	done
	echo "timed out waiting for $expectedCount recorded chunks" >&2
	return 1
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "announces the keyword pattern it listens for" {
	start_daemon
	wait_for_output "hey-bot: listening for keywords matching: clever|jarvis"
}

@test "records a transcription of three or more words with a timestamp in the current log" {
	queue_transcriptions "the coffee machine is running"
	start_daemon
	wait_for_file "$CURRENT_LOG_FILE"

	run grep -cE '^\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\] the coffee machine is running$' "$CURRENT_LOG_FILE"
	[ "$output" = "1" ]
}

@test "keeps a short transcription without a keyword out of the log" {
	queue_transcriptions "good morning" "the coffee machine is running"
	start_daemon
	wait_for_file "$CURRENT_LOG_FILE"

	run grep -c "good morning" "$CURRENT_LOG_FILE"
	[ "$output" = "0" ]
}

@test "skips transcription for a chunk below the energy threshold" {
	export AMPLITUDE_VALUE="0.010000"
	queue_transcriptions "hey clever what is the weather"
	start_daemon
	wait_for_recorded_chunks 4

	[ ! -f "$WHISPER_CALL_LOG" ]
	[ ! -f "$NOTIFY_CALL_LOG" ]
}

@test "discards a transcription that is mostly non-latin" {
	queue_transcriptions "こんにちは 世界 元気ですか" "the coffee machine is running"
	start_daemon
	wait_for_file "$CURRENT_LOG_FILE"

	run grep -c "こんにちは" "$CURRENT_LOG_FILE"
	[ "$output" = "0" ]
	grep -qF "the coffee machine is running" "$CURRENT_LOG_FILE"
}

@test "a detected keyword announces itself and asks the user to speak" {
	queue_transcriptions "hey clever are you there"
	start_daemon
	wait_for_output "hey-bot: keyword detected in: 'hey clever are you there'"
	wait_for_file "$NOTIFY_CALL_LOG"

	grep -qxF "Hey Bot|Listening..." "$NOTIFY_CALL_LOG"
}

@test "the disabled flag file suppresses keyword activation" {
	if [ -e "$KEYWORDS_DISABLED_FLAG_FILE" ]; then
		skip "another hey-bot run already owns $KEYWORDS_DISABLED_FLAG_FILE"
	fi
	KEYWORDS_DISABLED_FLAG_OWNED=1
	touch "$KEYWORDS_DISABLED_FLAG_FILE"

	queue_transcriptions "hey clever are you there" "" "" ""
	start_daemon
	wait_for_recorded_chunks 4

	run grep -c "keyword detected" "$DAEMON_OUTPUT"
	[ "$output" = "0" ]
}

@test "silence ends the command and sends the whole phrase to the gateway" {
	queue_transcriptions "hey clever what is the weather" "in florianopolis today" "" "" ""
	start_daemon
	wait_for_output "hey-bot: sending command to gateway in background"
	wait_for_file "$GATEWAY_REQUEST_LOG"

	run jq -r '.messages[0].content' "$GATEWAY_REQUEST_LOG"
	[[ "$output" == *"[Command:]"* ]]
	[[ "$output" == *"hey clever what is the weather in florianopolis today"* ]]
	run jq -r '.model' "$GATEWAY_REQUEST_LOG"
	[ "$output" = "test-model" ]
	run jq -r '.user' "$GATEWAY_REQUEST_LOG"
	[ "$output" = "voice-main" ]
}

@test "a command that never falls silent still ends at the chunk cap" {
	queue_transcriptions "hey clever count with me"
	local chunkIndex
	for chunkIndex in $(seq 1 15); do
		queue_transcriptions "one two three"
	done
	start_daemon
	wait_for_output "hey-bot: sending command to gateway in background"
}

@test "an empty command returns to listening without calling the gateway" {
	queue_transcriptions "hey clever" "" "" ""
	start_daemon
	wait_for_output "hey-bot: empty command, returning to listening"

	[ ! -f "$GATEWAY_REQUEST_LOG" ]
}

@test "a spoken response unmutes the sink and plays the rendered file" {
	respond_with_content "The weather is fine."
	queue_transcriptions "hey clever what is the weather" "in florianopolis today" "" "" ""
	start_daemon
	wait_for_file "$PLAYER_CALL_LOG"

	grep -qF "en-US-JennyNeural" "$TTS_CALL_LOG"
	grep -qF "The weather is fine." "$TTS_CALL_LOG"
	grep -qxF "set-mute @DEFAULT_AUDIO_SINK@ 0" "$SINK_CALL_LOG"
	grep -qF -- "--no-video --ao=pulse" "$PLAYER_CALL_LOG"
	grep -qF "[RESPONSE] The weather is fine." "$CURRENT_LOG_FILE"
}

@test "an IGNORE response skips text to speech" {
	respond_with_content "IGNORE"
	queue_transcriptions "hey clever mumble mumble" "grumble grumble grumble" "" "" ""
	start_daemon
	wait_for_output "hey-bot: nonsensical input, skipping TTS"

	[ ! -f "$TTS_CALL_LOG" ]
	[ ! -f "$PLAYER_CALL_LOG" ]
}

@test "a WAIT response keeps the context and prepends it to the next keyword" {
	respond_with_content "WAIT"
	queue_transcriptions "hey clever turn on the" "living room" "" "" ""
	start_daemon
	wait_for_output "hey-bot: mid-sentence detected, waiting for continuation"
	wait_for_followup_signal

	[ ! -f "$TTS_CALL_LOG" ]
	[ "$(cat "/tmp/hey-bot-wait-context-$DAEMON_PID")" = "hey clever turn on the living room" ]

	respond_with_content "Done."
	queue_transcriptions ""
	wait_for_output "hey-bot: follow-up window active"

	queue_transcriptions "please switch it now"
	wait_for_output "hey-bot: prepending wait context: 'hey clever turn on the living room'"
}

@test "a follow-up utterance of four or more words needs no keyword" {
	queue_transcriptions "hey clever say hello" "to everyone here" "" "" ""
	start_daemon
	wait_for_followup_signal

	queue_transcriptions ""
	wait_for_output "hey-bot: follow-up window active"

	queue_transcriptions "and also the kitchen light"
	wait_for_output "hey-bot: follow-up detected"
}

@test "the follow-up window expires after five quiet chunks" {
	queue_transcriptions "hey clever say hello" "to everyone here" "" "" ""
	start_daemon
	wait_for_followup_signal

	queue_transcriptions ""
	wait_for_output "hey-bot: follow-up window active"

	queue_transcriptions "" "" "" ""
	wait_for_output "hey-bot: follow-up window expired"
}

@test "an unreachable gateway speaks the reach failure" {
	: >"$GATEWAY_RESPONSE_FILE"
	queue_transcriptions "hey clever what is the weather" "in florianopolis today" "" "" ""
	start_daemon
	wait_for_output "Sorry, I could not reach the gateway."
	wait_for_file "$TTS_CALL_LOG"

	grep -qF "Sorry, I could not reach the gateway." "$TTS_CALL_LOG"
}

@test "an unparsable gateway response speaks the processing failure" {
	printf '{"error":"upstream exploded"}' >"$GATEWAY_RESPONSE_FILE"
	queue_transcriptions "hey clever what is the weather" "in florianopolis today" "" "" ""
	start_daemon
	wait_for_output "Sorry, I could not process that."
	wait_for_file "$TTS_CALL_LOG"

	grep -qF "hey-bot: gateway raw response: {\"error\":\"upstream exploded\"}" "$DAEMON_OUTPUT"
	grep -qF "Sorry, I could not process that." "$TTS_CALL_LOG"
}

@test "a text to speech failure skips playback" {
	export TTS_EXIT_CODE=1
	queue_transcriptions "hey clever what is the weather" "in florianopolis today" "" "" ""
	start_daemon
	wait_for_file "$TTS_CALL_LOG"
	wait_for_followup_signal

	[ ! -f "$PLAYER_CALL_LOG" ]
	[ ! -f "$SINK_CALL_LOG" ]
}

@test "an oversized current log is rotated to a timestamped file" {
	export HEY_BOT_MAX_LOG_SIZE=8
	printf 'an older transcription line\n' >"$CURRENT_LOG_FILE"

	queue_transcriptions "the coffee machine is running"
	start_daemon
	wait_for_output "hey-bot: listening"

	local attempt
	for attempt in $(seq 1 400); do
		if grep -qF "the coffee machine is running" "$CURRENT_LOG_FILE" 2>/dev/null; then break; fi
		/bin/sleep 0.02
	done

	run find "$HEY_BOT_TRANSCRIPTION_DIR" -maxdepth 1 -name '20*.log'
	[ -n "$output" ]
	grep -qF "an older transcription line" "$output"
	run grep -c "an older transcription line" "$CURRENT_LOG_FILE"
	[ "$output" = "0" ]
}
