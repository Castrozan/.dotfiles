#!/usr/bin/env bats

load '../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/hey-bot-test"
	export SCRIPT_UNDER_TEST
	REAL_MKTEMP="$(command -v mktemp)"
	export REAL_MKTEMP
	unset BASH_ENV

	export HOME="$BATS_TEST_TMPDIR/home"
	mkdir -p "$HOME"

	export HEY_BOT_WHISPER_MODEL="$BATS_TEST_TMPDIR/ggml-base.bin"
	export HEY_BOT_KEYWORDS_PROMPT="clever, jarvis"

	CACHE_DIRECTORY="$HOME/.cache/hey-bot-test"
	AUDIO_FILE="$BATS_TEST_TMPDIR/recording.wav"
	: >"$AUDIO_FILE"

	export WHISPER_CALL_LOG="$BATS_TEST_TMPDIR/whisper-calls.log"
	export WHISPER_OUTPUT="hey clever what is the weather"
	export SOX_CALL_LOG="$BATS_TEST_TMPDIR/sox-calls.log"
	export TTS_CALL_LOG="$BATS_TEST_TMPDIR/tts-calls.log"
	export CONVERTER_CALL_LOG="$BATS_TEST_TMPDIR/converter-calls.log"
	export AUDIO_DURATION=6
	export AMPLITUDE_VALUE="0.500000"
	export MKTEMP_PATH_LOG="$BATS_TEST_TMPDIR/mktemp-paths.log"

	FAKE_BIN_DIRECTORY="$BATS_TEST_TMPDIR/bin"
	mkdir -p "$FAKE_BIN_DIRECTORY"

	cat >"$FAKE_BIN_DIRECTORY/soxi" <<-'FAKE_SOXI'
		#!/usr/bin/env bash
		printf '%s\n' "$AUDIO_DURATION"
	FAKE_SOXI

	cat >"$FAKE_BIN_DIRECTORY/sox" <<-'FAKE_SOX'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$SOX_CALL_LOG"
		if [ "$2" = "-n" ] && [ "$3" = "stat" ]; then
			printf 'Maximum amplitude:     %s\n' "$AMPLITUDE_VALUE"
			exit 0
		fi
		outputPath=""
		previousArgument=""
		for argument in "$@"; do
			case "$argument" in
			trim | synth | vol)
				outputPath="$previousArgument"
				break
				;;
			esac
			previousArgument="$argument"
		done
		if [ -z "$outputPath" ]; then outputPath="${*: -1}"; fi
		: >"$outputPath"
	FAKE_SOX

	cat >"$FAKE_BIN_DIRECTORY/whisper-cli" <<-'FAKE_WHISPER'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$WHISPER_CALL_LOG"
		printf '%s\n' "$WHISPER_OUTPUT"
	FAKE_WHISPER

	cat >"$FAKE_BIN_DIRECTORY/edge-tts" <<-'FAKE_TTS'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$TTS_CALL_LOG"
		mediaPath=""
		while [ $# -gt 0 ]; do
			if [ "$1" = "--write-media" ]; then mediaPath="$2"; shift; fi
			shift
		done
		if [ -n "$mediaPath" ]; then : >"$mediaPath"; fi
	FAKE_TTS

	cat >"$FAKE_BIN_DIRECTORY/ffmpeg" <<-'FAKE_CONVERTER'
		#!/usr/bin/env bash
		printf '%s\n' "$*" >>"$CONVERTER_CALL_LOG"
		: >"${*: -1}"
	FAKE_CONVERTER

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
	if [ -f "$MKTEMP_PATH_LOG" ]; then
		while read -r temporaryPath; do rm -rf "$temporaryPath"; done <"$MKTEMP_PATH_LOG"
	fi
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "prints the usage without a command" {
	run_script_under_test
	[ "$status" -eq 1 ]
	[[ "$output" == *"Usage: hey-bot-test <command>"* ]]
	[[ "$output" == *"generate"* ]]
	[[ "$output" == *"sweep <audio-file>"* ]]
	[[ "$output" == *"run <audio-file> [flags]"* ]]
}

@test "prints the usage for an unknown command" {
	run_script_under_test measure
	[ "$status" -eq 1 ]
	[[ "$output" == *"Usage: hey-bot-test <command>"* ]]
}

@test "sweep without an audio file prints its own usage" {
	run_script_under_test sweep
	[ "$status" -eq 1 ]
	[ "$output" = "Usage: hey-bot-test sweep <audio-file>" ]
}

@test "run without an audio file prints its own usage" {
	run_script_under_test run
	[ "$status" -eq 1 ]
	[ "$output" = "Usage: hey-bot-test run <audio-file> [whisper-cli flags...]" ]
}

@test "sweep reports a missing audio file" {
	run_script_under_test sweep "$BATS_TEST_TMPDIR/absent.wav"
	[ "$status" -eq 1 ]
	[ "$output" = "File not found: $BATS_TEST_TMPDIR/absent.wav" ]
}

@test "run reports a missing audio file" {
	run_script_under_test run "$BATS_TEST_TMPDIR/absent.wav"
	[ "$status" -eq 1 ]
	[ "$output" = "File not found: $BATS_TEST_TMPDIR/absent.wav" ]
}

@test "sweep transcribes each chunk under all five configurations" {
	run_script_under_test sweep "$AUDIO_FILE"
	[ "$status" -eq 0 ]
	[[ "$output" == *"Audio: $AUDIO_FILE (6s, 1 chunks of 6s)"* ]]
	[[ "$output" == *"Chunk 1 (0:00-0:06) amplitude=0.500000"* ]]
	[[ "$output" == *"baseline:            hey clever what is the weather"* ]]
	[[ "$output" == *"with-prompt:         hey clever what is the weather"* ]]
	[[ "$output" == *"beam5:               hey clever what is the weather"* ]]
	[[ "$output" == *"beam5+prompt:        hey clever what is the weather"* ]]
	[[ "$output" == *"conservative:        hey clever what is the weather"* ]]

	run grep -c -- "--prompt clever, jarvis" "$WHISPER_CALL_LOG"
	[ "$output" = "2" ]
	run grep -c -- "-bs 5 -bo 5" "$WHISPER_CALL_LOG"
	[ "$output" = "2" ]
	grep -qF -- "--entropy-thold 2.0 --no-speech-thold 0.8" "$WHISPER_CALL_LOG"
}

@test "run passes the extra flags through to the transcriber" {
	run_script_under_test run "$AUDIO_FILE" -l en --best-of 3
	[ "$status" -eq 0 ]
	[[ "$output" == *"Chunk 1 (amplitude=0.500000): hey clever what is the weather"* ]]
	grep -qF -- "-nt -np -l en --best-of 3" "$WHISPER_CALL_LOG"
}

@test "run skips a chunk below the energy threshold" {
	export AMPLITUDE_VALUE="0.010000"
	run_script_under_test run "$AUDIO_FILE" -l en
	[ "$status" -eq 0 ]
	[ "$output" = "Chunk 1: [below energy threshold, amplitude=0.010000]" ]
	[ ! -f "$WHISPER_CALL_LOG" ]
}

@test "generate renders every sentence, mixes in noise and records the ground truth" {
	run_script_under_test generate
	[ "$status" -eq 0 ]
	[[ "$output" == *"Generated: $CACHE_DIRECTORY/test-audio.wav"* ]]
	[[ "$output" == *"Ground truth: $CACHE_DIRECTORY/ground-truth.txt"* ]]
	[[ "$output" == *"Duration: 6s"* ]]

	run grep -c "en-US-JennyNeural" "$TTS_CALL_LOG"
	[ "$output" = "2" ]
	run grep -c "pt-BR-FranciscaNeural" "$TTS_CALL_LOG"
	[ "$output" = "2" ]
	run wc -l <"$CONVERTER_CALL_LOG"
	[ "${output// /}" = "4" ]

	grep -qF "synth 6 pinknoise vol 0.05" "$SOX_CALL_LOG"
	grep -qF -- "-m $CACHE_DIRECTORY/clean-audio.wav $CACHE_DIRECTORY/noise.wav $CACHE_DIRECTORY/test-audio.wav" "$SOX_CALL_LOG"
	[ -f "$CACHE_DIRECTORY/test-audio.wav" ]

	run cat "$CACHE_DIRECTORY/ground-truth.txt"
	[[ "$output" == "Segment 1 (EN): Hey clever, what is the weather like today?"* ]]
	[[ "$output" == *"Segment 4 (PT): Me conta as ultimas noticias" ]]
}
