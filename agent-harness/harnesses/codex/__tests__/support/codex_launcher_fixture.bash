setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/codex"
	WRAPPER_SHELL="$BASH"
	TEMPORARY_ROOT="$(mktemp -d)"
	FAKE_BINARY_DIRECTORY="$TEMPORARY_ROOT/bin"
	GLOBAL_INSTRUCTIONS_FILE="$TEMPORARY_ROOT/global-instructions.md"
	PROFILE_INSTRUCTIONS_FILE="$TEMPORARY_ROOT/profile-instructions.md"
	DISPATCH_FILE="$TEMPORARY_ROOT/workspace-profile-dispatch"
	DISPATCH_MARKER="$TEMPORARY_ROOT/dispatch-was-sourced"
	PRIVATE_LAUNCH_MARKER="$TEMPORARY_ROOT/private-launch"
	HOOK_TRUST_ARGUMENTS_FILE="$TEMPORARY_ROOT/hook-trust-arguments"
	mkdir -p "$FAKE_BINARY_DIRECTORY"
	printf 'global instructions' >"$GLOBAL_INSTRUCTIONS_FILE"
	printf 'profile instructions' >"$PROFILE_INSTRUCTIONS_FILE"

	cat >"$FAKE_BINARY_DIRECTORY/codex" <<-'FAKE_CODEX'
		#!/usr/bin/env bash
		printf 'argv:'
		printf ' <%s>' "$@"
		printf '\n'
		printf 'AGENT_INTERACTIVE_PREFERENCES_PATH=<%s>\n' "${AGENT_INTERACTIVE_PREFERENCES_PATH-unset}"
		printf 'NPM_CONFIG_PREFIX=<%s>\n' "${NPM_CONFIG_PREFIX-unset}"
		printf 'CODEX_SESSION_SOCKET_PATH=<%s>\n' "${CODEX_SESSION_SOCKET_PATH-unset}"
	FAKE_CODEX

	chmod +x "$FAKE_BINARY_DIRECTORY/codex"
	cat >"$FAKE_BINARY_DIRECTORY/approve-hooks" <<-'FAKE_APPROVAL'
		#!/usr/bin/env bash
		printf '<%s>\n' "$@" >"$HOOK_TRUST_ARGUMENTS_FILE"
		exit "${HOOK_TRUST_EXIT_STATUS:-0}"
	FAKE_APPROVAL
	chmod +x "$FAKE_BINARY_DIRECTORY/approve-hooks"
	cat >"$FAKE_BINARY_DIRECTORY/private-session" <<-'FAKE_PRIVATE'
		#!/usr/bin/env bash
		touch "$PRIVATE_LAUNCH_MARKER"
		exec "$CODEX_LAUNCHER_BINARY" "$@"
	FAKE_PRIVATE
	chmod +x "$FAKE_BINARY_DIRECTORY/private-session"
	write_dispatch_file
}

teardown() {
	rm -rf "$TEMPORARY_ROOT"
}

write_dispatch_file() {
	{
		printf 'touch "$DISPATCH_MARKER"\n'
		printf '%s\n' "$@"
	} >"$DISPATCH_FILE"
}

run_codex() {
	run env -i \
		PATH="$FAKE_BINARY_DIRECTORY:$PATH" \
		DISPATCH_MARKER="$DISPATCH_MARKER" \
		NPM_CONFIG_PREFIX="/nonexistent" \
		CODEX_SESSION_SOCKET_PATH="/tmp/inherited-parent.sock" \
		CODEX_LAUNCHER_DEVELOPER_INSTRUCTIONS_FILE="$GLOBAL_INSTRUCTIONS_FILE" \
		CODEX_LAUNCHER_WORKSPACE_PROFILE_DISPATCH_FILE="$DISPATCH_FILE" \
		PRIVATE_LAUNCH_MARKER="$PRIVATE_LAUNCH_MARKER" \
		CODEX_LAUNCHER_SESSION_EXECUTABLE="$FAKE_BINARY_DIRECTORY/private-session" \
		CODEX_LAUNCHER_BINARY="$FAKE_BINARY_DIRECTORY/codex" \
		CODEX_LAUNCHER_HOOK_TRUST_EXECUTABLE="$FAKE_BINARY_DIRECTORY/approve-hooks" \
		HOOK_TRUST_ARGUMENTS_FILE="$HOOK_TRUST_ARGUMENTS_FILE" \
		HOOK_TRUST_EXIT_STATUS="${HOOK_TRUST_EXIT_STATUS:-0}" \
		"$WRAPPER_SHELL" "$SCRIPT_UNDER_TEST" "$@"
}

launcher_arguments() {
	echo '<--sandbox> <danger-full-access> <--ask-for-approval> <never>'
}
