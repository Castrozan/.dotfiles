#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	TWITTER_SCRIPTS_DIRECTORY="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts"
	SCRIPT_UNDER_TEST="$TWITTER_SCRIPTS_DIRECTORY/twikit-cli-entrypoint.sh"
	WRAPPER_SHELL="$BASH"
	TEMPORARY_ROOT="$(mktemp -d)"
	FAKE_BINARY_DIRECTORY="$TEMPORARY_ROOT/bin"
	FAKE_HOME_DIRECTORY="$TEMPORARY_ROOT/home"
	VIRTUALENV_DIRECTORY="$FAKE_HOME_DIRECTORY/.local/share/twikit-venv"
	SECRETS_DIRECTORY="$FAKE_HOME_DIRECTORY/.secrets"
	COOKIES_PATH="$FAKE_HOME_DIRECTORY/.config/twikit/cookies.json"
	COMMAND_LOG="$TEMPORARY_ROOT/commands.log"
	mkdir -p "$FAKE_BINARY_DIRECTORY" "$SECRETS_DIRECTORY" "$VIRTUALENV_DIRECTORY/bin"
	: >"$COMMAND_LOG"

	cat >"$FAKE_BINARY_DIRECTORY/python" <<-'FAKE_PYTHON'
		#!/usr/bin/env bash
		echo "python $*" >>"$COMMAND_LOG"
		if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then
			mkdir -p "$3/bin"
			cp "$FAKE_BINARY_DIRECTORY/venv-python" "$3/bin/python"
		fi
	FAKE_PYTHON

	cat >"$FAKE_BINARY_DIRECTORY/sed" <<-'FAKE_SED'
		#!/usr/bin/env bash
		echo "sed $*" >>"$COMMAND_LOG"
	FAKE_SED

	cat >"$FAKE_BINARY_DIRECTORY/venv-python" <<-'FAKE_VENV_PYTHON'
		#!/usr/bin/env bash
		echo "venv-python $*" >>"$COMMAND_LOG"
	FAKE_VENV_PYTHON

	cat >"$VIRTUALENV_DIRECTORY/bin/pip" <<-'FAKE_PIP'
		#!/usr/bin/env bash
		echo "pip $*" >>"$COMMAND_LOG"
		if [ "$1" = "show" ]; then
			if [ -z "${FAKE_INSTALLED_TWIKIT_VERSION:-}" ]; then
				exit 1
			fi
			echo "Name: twikit"
			echo "Version: $FAKE_INSTALLED_TWIKIT_VERSION"
		fi
	FAKE_PIP

	chmod +x "$FAKE_BINARY_DIRECTORY"/* "$VIRTUALENV_DIRECTORY/bin/pip"
	cp "$FAKE_BINARY_DIRECTORY/venv-python" "$VIRTUALENV_DIRECTORY/bin/python"

	provide_grep_supporting_pcre
}

provide_grep_supporting_pcre() {
	local candidate
	for candidate in $(type -a -p grep 2>/dev/null) $(type -a -p ggrep 2>/dev/null); do
		if echo "Version: probe" | "$candidate" -oP 'Version: \K.*' >/dev/null 2>&1; then
			ln -sf "$candidate" "$FAKE_BINARY_DIRECTORY/grep"
			return
		fi
	done

	cat >"$FAKE_BINARY_DIRECTORY/grep" <<-'STAND_IN_GREP'
		#!/usr/bin/env bash
		if [ "$1" != "-oP" ] || [ "$2" != 'Version: \K.*' ]; then
			echo "stand-in grep only covers the pinned version lookup" >&2
			exit 2
		fi
		matchStatus=1
		while IFS= read -r line; do
			if [ "${line#Version: }" != "$line" ]; then
				echo "${line#Version: }"
				matchStatus=0
			fi
		done
		exit "$matchStatus"
	STAND_IN_GREP
	chmod +x "$FAKE_BINARY_DIRECTORY/grep"
}

teardown() {
	rm -rf "$TEMPORARY_ROOT"
}

run_twikit_cli() {
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
		TWIKIT_VERSION="2.3.3" \
		TWIKIT_VIRTUALENV_PATH="$VIRTUALENV_DIRECTORY" \
		TWIKIT_COOKIES_PATH="$COOKIES_PATH" \
		TWIKIT_SECRETS_DIRECTORY="$SECRETS_DIRECTORY" \
		TWIKIT_SCRIPTS_DIRECTORY="$TWITTER_SCRIPTS_DIRECTORY" \
		"${environmentOverrides[@]}" \
		"$WRAPPER_SHELL" "$SCRIPT_UNDER_TEST" "$@"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "runs the cli without reinstalling when the pinned version is already installed" {
	run_twikit_cli FAKE_INSTALLED_TWIKIT_VERSION="2.3.3" timeline
	[ "$status" -eq 0 ]
	[[ "$output" != *"Installing twikit"* ]]
	run grep -F "venv-python $TWITTER_SCRIPTS_DIRECTORY/twikit-cli.py timeline" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
	run grep -F "pip install" "$COMMAND_LOG"
	[ "$status" -ne 0 ]
}

@test "reinstalls and patches when the installed version differs from the pinned one" {
	run_twikit_cli FAKE_INSTALLED_TWIKIT_VERSION="2.0.0"
	[ "$status" -eq 0 ]
	[[ "$output" == *"[nix] Installing twikit 2.3.3..."* ]]
	run grep -F "pip install --quiet --upgrade twikit==2.3.3 pycryptodome secretstorage" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
}

@test "reinstalls when the virtualenv interpreter is missing" {
	rm -f "$VIRTUALENV_DIRECTORY/bin/python"
	run_twikit_cli FAKE_INSTALLED_TWIKIT_VERSION="2.3.3"
	[ "$status" -eq 0 ]
	[[ "$output" == *"[nix] Installing twikit 2.3.3..."* ]]
	run grep -F "python -m venv $VIRTUALENV_DIRECTORY" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
}

@test "patches the twikit client and user modules and runs the transaction patch on reinstall" {
	mkdir -p "$VIRTUALENV_DIRECTORY/lib/python3.12/site-packages/twikit/client"
	: >"$VIRTUALENV_DIRECTORY/lib/python3.12/site-packages/twikit/client/client.py"
	: >"$VIRTUALENV_DIRECTORY/lib/python3.12/site-packages/twikit/user.py"
	run_twikit_cli FAKE_INSTALLED_TWIKIT_VERSION="2.0.0"
	[ "$status" -eq 0 ]
	run grep -F "site-packages/twikit/client/client.py" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
	run grep -F "site-packages/twikit/user.py" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
	run grep -F "venv-python $TWITTER_SCRIPTS_DIRECTORY/patch-twikit-transaction.py $VIRTUALENV_DIRECTORY" "$COMMAND_LOG"
	[ "$status" -ne 0 ]
	run grep -F "python $TWITTER_SCRIPTS_DIRECTORY/patch-twikit-transaction.py $VIRTUALENV_DIRECTORY" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
}

@test "seeds the cookies file from the secrets directory when it is absent" {
	printf 'seeded-cookie-payload' >"$SECRETS_DIRECTORY/x-cookies"
	run_twikit_cli FAKE_INSTALLED_TWIKIT_VERSION="2.3.3"
	[ "$status" -eq 0 ]
	[[ "$output" == *"[nix] Seeded cookies from agenix secret"* ]]
	[ "$(cat "$COOKIES_PATH")" = "seeded-cookie-payload" ]
	run find "$COOKIES_PATH" -perm 600
	[ "$output" = "$COOKIES_PATH" ]
}

@test "leaves an existing cookies file untouched" {
	mkdir -p "$(dirname "$COOKIES_PATH")"
	printf 'existing-cookie-payload' >"$COOKIES_PATH"
	printf 'seeded-cookie-payload' >"$SECRETS_DIRECTORY/x-cookies"
	run_twikit_cli FAKE_INSTALLED_TWIKIT_VERSION="2.3.3"
	[ "$status" -eq 0 ]
	[[ "$output" != *"Seeded cookies"* ]]
	[ "$(cat "$COOKIES_PATH")" = "existing-cookie-payload" ]
}

@test "runs the cookie extractor instead of the cli for the extract-cookies subcommand" {
	run_twikit_cli FAKE_INSTALLED_TWIKIT_VERSION="2.3.3" extract-cookies
	[ "$status" -eq 0 ]
	run grep -F "venv-python $TWITTER_SCRIPTS_DIRECTORY/extract-x-cookies.py" "$COMMAND_LOG"
	[ "$status" -eq 0 ]
}
