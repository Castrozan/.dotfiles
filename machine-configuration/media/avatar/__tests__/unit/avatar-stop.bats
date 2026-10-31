#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	FAKE_BIN_DIRECTORY="$BATS_TEST_TMPDIR/bin"
	mkdir -p "$FAKE_BIN_DIRECTORY"

	export CALL_LOG="$BATS_TEST_TMPDIR/calls.log"
	export SYSTEMCTL_EXIT_STATUS=0
	export AVATAR_AUDIO_EXIT_STATUS=0

	cat >"$FAKE_BIN_DIRECTORY/systemctl" <<-'FAKE_SYSTEMCTL'
		#!/usr/bin/env bash
		echo "systemctl $*" >>"$CALL_LOG"
		exit "$SYSTEMCTL_EXIT_STATUS"
	FAKE_SYSTEMCTL

	cat >"$FAKE_BIN_DIRECTORY/avatar-audio" <<-'FAKE_AVATAR_AUDIO'
		#!/usr/bin/env bash
		echo "avatar-audio $*" >>"$CALL_LOG"
		exit "$AVATAR_AUDIO_EXIT_STATUS"
	FAKE_AVATAR_AUDIO

	chmod +x "$FAKE_BIN_DIRECTORY"/*
	PATH="$FAKE_BIN_DIRECTORY:$PATH"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "stops the target and every owned service in one job before audio cleanup" {
	run_script_under_test

	[ "$status" -eq 0 ]
	grep -qxF "systemctl --user stop avatar.target avatar-camera.service avatar-control-server.service avatar-renderer.service avatar-audio.service" "$CALL_LOG"
	[ "$(tail -n 1 "$CALL_LOG")" = "avatar-audio stop" ]
}

@test "reports the audio refusal while agent playback is connected" {
	export AVATAR_AUDIO_EXIT_STATUS=3

	run_script_under_test

	[ "$status" -eq 3 ]
}

@test "still cleans audio when stopping services fails and keeps that failure" {
	export SYSTEMCTL_EXIT_STATUS=5

	run_script_under_test

	[ "$status" -eq 5 ]
	[ "$(tail -n 1 "$CALL_LOG")" = "avatar-audio stop" ]
}
