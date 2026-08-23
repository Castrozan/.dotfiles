#!/usr/bin/env bats

load '../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/hey-bot-log"
	export SCRIPT_UNDER_TEST
	unset BASH_ENV

	export HOME="$BATS_TEST_TMPDIR/home"
	export HEY_BOT_TRANSCRIPTION_DIR="$HOME/.local/share/hey-bot/transcriptions"
	mkdir -p "$HEY_BOT_TRANSCRIPTION_DIR"

	export FOLLOW_CALL_LOG="$BATS_TEST_TMPDIR/follow-calls.log"

	FAKE_BIN_DIRECTORY="$BATS_TEST_TMPDIR/bin"
	mkdir -p "$FAKE_BIN_DIRECTORY"

	cat >"$FAKE_BIN_DIRECTORY/tail" <<-'FAKE_TAIL'
		#!/usr/bin/env bash
		if [ "$1" = "-f" ]; then
			printf '%s\n' "$2" >>"$FOLLOW_CALL_LOG"
			exit 0
		fi
		exec /usr/bin/tail "$@"
	FAKE_TAIL

	chmod +x "$FAKE_BIN_DIRECTORY"/*
	PATH="$FAKE_BIN_DIRECTORY:$PATH"
}

require_timestamp_printing_find() {
	if ! find "$HEY_BOT_TRANSCRIPTION_DIR" -maxdepth 1 -printf '%T@\n' >/dev/null 2>&1; then
		skip "needs GNU find -printf; hey-bot is a Linux-only capability"
	fi
}

write_log_file() {
	printf '%s\n' "$2" >"$HEY_BOT_TRANSCRIPTION_DIR/$1"
	touch -t "$3" "$HEY_BOT_TRANSCRIPTION_DIR/$1"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "reports the empty transcription directory and fails" {
	require_timestamp_printing_find
	run_script_under_test
	[ "$status" -eq 1 ]
	[[ "$output" == *"No transcription logs found in $HEY_BOT_TRANSCRIPTION_DIR"* ]]
}

@test "ignores files that are not transcription logs" {
	require_timestamp_printing_find
	printf 'not a log\n' >"$HEY_BOT_TRANSCRIPTION_DIR/notes.txt"

	run_script_under_test
	[ "$status" -eq 1 ]
	[[ "$output" == *"No transcription logs found"* ]]
}

@test "prints the newest log" {
	require_timestamp_printing_find
	write_log_file "2026-08-20_10-00-00.log" "the older transcription" 202608201000
	write_log_file "current.log" "the newest transcription" 202608231900

	run_script_under_test
	[ "$status" -eq 0 ]
	[ "$output" = "the newest transcription" ]
}

@test "follows the newest log when asked" {
	require_timestamp_printing_find
	write_log_file "current.log" "the newest transcription" 202608231900

	run_script_under_test -f
	[ "$status" -eq 0 ]
	grep -qxF "$HEY_BOT_TRANSCRIPTION_DIR/current.log" "$FOLLOW_CALL_LOG"
}

@test "reads only the top level of the transcription directory" {
	require_timestamp_printing_find
	mkdir -p "$HEY_BOT_TRANSCRIPTION_DIR/archive"
	write_log_file "archive/2026-08-22_10-00-00.log" "the archived transcription" 202608231930
	write_log_file "current.log" "the newest transcription" 202608231900

	run_script_under_test
	[ "$status" -eq 0 ]
	[ "$output" = "the newest transcription" ]
}
