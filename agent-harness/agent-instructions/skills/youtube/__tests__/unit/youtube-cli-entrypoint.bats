#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	YOUTUBE_SCRIPTS_DIRECTORY="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts"
	SCRIPT_UNDER_TEST="$YOUTUBE_SCRIPTS_DIRECTORY/youtube-cli-entrypoint.sh"
	WRAPPER_SHELL="$BASH"
	TEMPORARY_ROOT="$(mktemp -d)"
	FAKE_BINARY_DIRECTORY="$TEMPORARY_ROOT/bin"
	FAKE_HOME_DIRECTORY="$TEMPORARY_ROOT/home"
	VIRTUALENV_DIRECTORY="$FAKE_HOME_DIRECTORY/.local/share/youtube-cli-venv"
	CLI_SCRIPT="$TEMPORARY_ROOT/youtube-cli.py"
	SETUP_SCRIPT="$TEMPORARY_ROOT/youtube-cli-setup.sh"
	COMMAND_LOG="$TEMPORARY_ROOT/commands.log"
	mkdir -p "$FAKE_BINARY_DIRECTORY" "$VIRTUALENV_DIRECTORY/bin"
	: >"$COMMAND_LOG"
	: >"$CLI_SCRIPT"

	cat >"$SETUP_SCRIPT" <<-'FAKE_SETUP'
		#!/usr/bin/env bash
		echo "ran-the-setup-script"
	FAKE_SETUP

	cat >"$FAKE_BINARY_DIRECTORY/python" <<-'FAKE_PYTHON'
		#!/usr/bin/env bash
		echo "python $*" >>"$COMMAND_LOG"
		if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then
			mkdir -p "$3/bin"
			cp "$FAKE_BINARY_DIRECTORY/venv-python" "$3/bin/python"
		fi
	FAKE_PYTHON

	cat >"$FAKE_BINARY_DIRECTORY/venv-python" <<-'FAKE_VENV_PYTHON'
		#!/usr/bin/env bash
		echo "venv-python $*" >>"$COMMAND_LOG"
	FAKE_VENV_PYTHON

	cat >"$VIRTUALENV_DIRECTORY/bin/pip" <<-'FAKE_PIP'
		#!/usr/bin/env bash
		echo "pip $*" >>"$COMMAND_LOG"
		if [ "$1" = "show" ] && [ -z "${FAKE_GOOGLE_CLIENT_INSTALLED:-}" ]; then
			exit 1
		fi
	FAKE_PIP

	chmod +x "$FAKE_BINARY_DIRECTORY"/* "$VIRTUALENV_DIRECTORY/bin/pip"
	cp "$FAKE_BINARY_DIRECTORY/venv-python" "$VIRTUALENV_DIRECTORY/bin/python"
	ln -sf "$WRAPPER_SHELL" "$FAKE_BINARY_DIRECTORY/bash"
}

teardown() {
	rm -rf "$TEMPORARY_ROOT"
}

run_youtube_cli() {
	local -a environmentOverrides=()
	while [ "$#" -gt 0 ] && [[ "$1" == *=* ]]; do
		environmentOverrides+=("$1")
		shift
	done
	run env -i \
		HOME="$FAKE_HOME_DIRECTORY" \
		PATH="$FAKE_BINARY_DIRECTORY:$PATH" \
		COMMAND_LOG="$COMMAND_LOG" \
		FAKE_BINARY_DIRECTORY="$FAKE_BINARY_DIRECTORY" \
		YOUTUBE_CLI_VIRTUALENV_PATH="$VIRTUALENV_DIRECTORY" \
		YOUTUBE_CLI_SCRIPT="$CLI_SCRIPT" \
		YOUTUBE_CLI_SETUP_SCRIPT="$SETUP_SCRIPT" \
		"${environmentOverrides[@]}" \
		"$WRAPPER_SHELL" "$SCRIPT_UNDER_TEST" "$@"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "hands the setup subcommand to the setup script without touching the virtualenv" {
	run_youtube_cli setup
	[ "$status" -eq 0 ]
	[[ "$output" == *"ran-the-setup-script"* ]]
	[ ! -s "$COMMAND_LOG" ]
}

@test "runs the cli without installing when the google api client is already present" {
	run_youtube_cli FAKE_GOOGLE_CLIENT_INSTALLED=1 search cats
	[ "$status" -eq 0 ]
	[[ "$output" != *"Installing youtube-cli dependencies"* ]]
	run grep -F "venv-python $CLI_SCRIPT search cats" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
	run grep -F "pip install" "$COMMAND_LOG"
	[ "$status" -ne 0 ]
}

@test "installs the google api dependencies when the client is missing" {
	run_youtube_cli search cats
	[ "$status" -eq 0 ]
	[[ "$output" == *"[nix] Installing youtube-cli dependencies..."* ]]
	run grep -F "pip install --quiet --upgrade google-api-python-client google-auth-oauthlib google-auth-httplib2" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
}

@test "creates the virtualenv when its interpreter is missing" {
	rm -f "$VIRTUALENV_DIRECTORY/bin/python"
	run_youtube_cli FAKE_GOOGLE_CLIENT_INSTALLED=1
	[ "$status" -eq 0 ]
	run grep -F "python -m venv $VIRTUALENV_DIRECTORY" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
}
