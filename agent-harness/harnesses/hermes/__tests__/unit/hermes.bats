#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/hermes"
	WRAPPER_SHELL="$BASH"
	TEMPORARY_ROOT="$(mktemp -d)"
	FAKE_BINARY_DIRECTORY="$TEMPORARY_ROOT/bin"
	LAUNCH_SCRIPT="$TEMPORARY_ROOT/hermes-launch"
	mkdir -p "$FAKE_BINARY_DIRECTORY"
	: >"$LAUNCH_SCRIPT"

	cat >"$FAKE_BINARY_DIRECTORY/fake-bash" <<-'FAKE_BASH'
		#!/usr/bin/env bash
		printf 'argv:'
		printf ' <%s>' "$@"
		printf '\n'
		printf 'HERMES_AGENT_VERSION=<%s>\n' "${HERMES_AGENT_VERSION-unset}"
		printf 'HERMES_AGENT_RUNTIME_PATH=<%s>\n' "${HERMES_AGENT_RUNTIME_PATH-unset}"
	FAKE_BASH

	chmod +x "$FAKE_BINARY_DIRECTORY/fake-bash"
}

teardown() {
	rm -rf "$TEMPORARY_ROOT"
}

run_hermes() {
	run env -i \
		PATH="$FAKE_BINARY_DIRECTORY:$PATH" \
		HERMES_AGENT_VERSION="0.19.0" \
		HERMES_AGENT_RUNTIME_PATH="/fake/coreutils/bin:/fake/git/bin" \
		HERMES_AGENT_BASH="$FAKE_BINARY_DIRECTORY/fake-bash" \
		HERMES_AGENT_LAUNCH_SCRIPT="$LAUNCH_SCRIPT" \
		"$WRAPPER_SHELL" "$SCRIPT_UNDER_TEST" "$@"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "runs the launch script through the pinned bash when given no arguments" {
	run_hermes
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "argv: <$LAUNCH_SCRIPT>" ]
}

@test "passes caller arguments through to the launch script" {
	run_hermes --resume "a prompt"
	[ "${lines[0]}" = "argv: <$LAUNCH_SCRIPT> <--resume> <a prompt>" ]
}

@test "hands the launcher environment to the launch script" {
	run_hermes
	[ "${lines[1]}" = 'HERMES_AGENT_VERSION=<0.19.0>' ]
	[ "${lines[2]}" = 'HERMES_AGENT_RUNTIME_PATH=</fake/coreutils/bin:/fake/git/bin>' ]
}

@test "preserves caller arguments that contain spaces and quotes" {
	run_hermes 'a "quoted" argument'
	[ "${lines[0]}" = "argv: <$LAUNCH_SCRIPT> <a \"quoted\" argument>" ]
}
