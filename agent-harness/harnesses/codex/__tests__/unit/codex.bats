#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/codex"
	WRAPPER_SHELL="$BASH"
	TEMPORARY_ROOT="$(mktemp -d)"
	FAKE_BINARY_DIRECTORY="$TEMPORARY_ROOT/bin"
	GLOBAL_INSTRUCTIONS_FILE="$TEMPORARY_ROOT/global-instructions.md"
	PROFILE_INSTRUCTIONS_FILE="$TEMPORARY_ROOT/profile-instructions.md"
	DISPATCH_FILE="$TEMPORARY_ROOT/workspace-profile-dispatch"
	DISPATCH_MARKER="$TEMPORARY_ROOT/dispatch-was-sourced"
	TPUT_LOG="$TEMPORARY_ROOT/tput.log"
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
		exit "${FAKE_CODEX_EXIT_STATUS:-0}"
	FAKE_CODEX
	cat >"$FAKE_BINARY_DIRECTORY/tput" <<-'FAKE_TPUT'
		#!/usr/bin/env bash
		printf '%s\n' "$1" >>"$TPUT_LOG"
	FAKE_TPUT

	chmod +x "$FAKE_BINARY_DIRECTORY/codex" "$FAKE_BINARY_DIRECTORY/tput"
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
		CODEX_LAUNCHER_DEVELOPER_INSTRUCTIONS_FILE="$GLOBAL_INSTRUCTIONS_FILE" \
		CODEX_LAUNCHER_WORKSPACE_PROFILE_DISPATCH_FILE="$DISPATCH_FILE" \
		CODEX_LAUNCHER_BINARY="$FAKE_BINARY_DIRECTORY/codex" \
		"$WRAPPER_SHELL" "$SCRIPT_UNDER_TEST" "$@"
}

run_codex_in_terminal() {
	local quotedCommand
	printf -v quotedCommand '%q ' "$WRAPPER_SHELL" "$SCRIPT_UNDER_TEST" "$@"
	run env -i \
		PATH="$FAKE_BINARY_DIRECTORY:$PATH" \
		DISPATCH_MARKER="$DISPATCH_MARKER" \
		TPUT_LOG="$TPUT_LOG" \
		FAKE_CODEX_EXIT_STATUS="${FAKE_CODEX_EXIT_STATUS:-0}" \
		NPM_CONFIG_PREFIX="/nonexistent" \
		CODEX_LAUNCHER_DEVELOPER_INSTRUCTIONS_FILE="$GLOBAL_INSTRUCTIONS_FILE" \
		CODEX_LAUNCHER_WORKSPACE_PROFILE_DISPATCH_FILE="$DISPATCH_FILE" \
		CODEX_LAUNCHER_BINARY="$FAKE_BINARY_DIRECTORY/codex" \
		script --quiet --return --command "$quotedCommand" /dev/null
}

pinned_arguments() {
	echo '<--model> <gpt-5.6-sol> <--sandbox> <danger-full-access> <--ask-for-approval> <never>'
}

@test "passes shellcheck apart from the dispatch file it sources by path" {
	if ! command -v shellcheck &>/dev/null; then
		skip "shellcheck not installed"
	fi
	run shellcheck --exclude=SC1090 "$SCRIPT_UNDER_TEST"
	[ "$status" -eq 0 ]
}

@test "starts codex on the pinned model, sandbox and approval policy" {
	run_codex
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "argv: $(pinned_arguments) <-c> <developer_instructions=global instructions>" ]
}

@test "keeps an interactive terminal session in one alternate buffer" {
	run_codex_in_terminal
	[ "$status" -eq 0 ]
	[ "$(sed -n '1p' "$TPUT_LOG")" = 'smcup' ]
	[ "$(sed -n '2p' "$TPUT_LOG")" = 'rmcup' ]
	[[ "$output" == *'<--no-alt-screen>'* ]]
}

@test "does not wrap a non-interactive subcommand in an alternate buffer" {
	run_codex_in_terminal exec "do the thing"
	[ "$status" -eq 0 ]
	[ ! -e "$TPUT_LOG" ]
	[[ "$output" != *'<--no-alt-screen>'* ]]
}

@test "does not hide help output in an alternate buffer" {
	run_codex_in_terminal --help
	[ "$status" -eq 0 ]
	[ ! -e "$TPUT_LOG" ]
	[[ "$output" != *'<--no-alt-screen>'* ]]
}

@test "restores the terminal buffer after Codex fails" {
	FAKE_CODEX_EXIT_STATUS=23 run_codex_in_terminal
	[ "$status" -eq 23 ]
	[ "$(sed -n '1p' "$TPUT_LOG")" = 'smcup' ]
	[ "$(sed -n '2p' "$TPUT_LOG")" = 'rmcup' ]
}

@test "exports the developer instructions path it injected" {
	run_codex
	[ "${lines[1]}" = "AGENT_INTERACTIVE_PREFERENCES_PATH=<$GLOBAL_INSTRUCTIONS_FILE>" ]
}

@test "hands the launcher environment through to codex" {
	run_codex
	[ "${lines[2]}" = 'NPM_CONFIG_PREFIX=</nonexistent>' ]
}

@test "sources the workspace profile dispatch on an interactive launch" {
	run_codex
	[ -f "$DISPATCH_MARKER" ]
}

@test "injects the developer instructions the dispatch resolved" {
	write_dispatch_file "codexDeveloperInstructionsFile=$PROFILE_INSTRUCTIONS_FILE"
	run_codex
	[ "${lines[0]}" = "argv: $(pinned_arguments) <-c> <developer_instructions=profile instructions>" ]
	[ "${lines[1]}" = "AGENT_INTERACTIVE_PREFERENCES_PATH=<$PROFILE_INSTRUCTIONS_FILE>" ]
}

@test "appends the workspace profile arguments after the interactive preferences" {
	write_dispatch_file "workspaceProfileArguments+=(-c 'model_reasoning_effort=\"high\"')"
	run_codex
	[ "${lines[0]}" = "argv: $(pinned_arguments) <-c> <developer_instructions=global instructions> <-c> <model_reasoning_effort=\"high\">" ]
}

@test "passes caller arguments through after every injected argument" {
	write_dispatch_file "workspaceProfileArguments+=(-c 'model_reasoning_effort=\"high\"')"
	run_codex resume --last
	[ "${lines[0]}" = "argv: $(pinned_arguments) <-c> <developer_instructions=global instructions> <-c> <model_reasoning_effort=\"high\"> <resume> <--last>" ]
}

@test "treats a leading flag as an interactive launch" {
	run_codex --search
	[ "${lines[0]}" = "argv: $(pinned_arguments) <-c> <developer_instructions=global instructions> <--search>" ]
}

@test "treats fork as an interactive launch" {
	run_codex fork
	[ "${lines[0]}" = "argv: $(pinned_arguments) <-c> <developer_instructions=global instructions> <fork>" ]
}

@test "leaves a subcommand launch without interactive preferences or profile activation" {
	run_codex exec "do the thing"
	[ "${lines[0]}" = "argv: $(pinned_arguments) <exec> <do the thing>" ]
	[ "${lines[1]}" = 'AGENT_INTERACTIVE_PREFERENCES_PATH=<unset>' ]
	[ ! -f "$DISPATCH_MARKER" ]
}

@test "preserves caller arguments that contain spaces and quotes" {
	run_codex exec 'a "quoted" argument'
	[ "${lines[0]}" = "argv: $(pinned_arguments) <exec> <a \"quoted\" argument>" ]
}
