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

@test "passes shellcheck apart from the dispatch file it sources by path" {
	if ! command -v shellcheck &>/dev/null; then
		skip "shellcheck not installed"
	fi
	run shellcheck --exclude=SC1090 "$SCRIPT_UNDER_TEST"
	[ "$status" -eq 0 ]
}

@test "selects a private interactive server without overriding its remembered model" {
	run_codex
	[ "$status" -eq 0 ]
	[ -f "$PRIVATE_LAUNCH_MARKER" ]
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive>" ]
}

@test "exports the selected instruction path for interactive hooks" {
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

@test "selects the workspace instruction profile the dispatch resolved" {
	write_dispatch_file "codexDeveloperInstructionsFile=$PROFILE_INSTRUCTIONS_FILE" \
		'codexInteractiveProfile=dotfiles-workspace-test'
	run_codex
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-workspace-test>" ]
	[ "${lines[1]}" = "AGENT_INTERACTIVE_PREFERENCES_PATH=<$PROFILE_INSTRUCTIONS_FILE>" ]
}

@test "lets an explicit caller profile replace the generated default" {
	for profile_argument in '--profile=custom' '-pcustom'; do
		run_codex "$profile_argument"
		[ "${lines[0]}" = "argv: $(launcher_arguments) <$profile_argument>" ]
	done
	for profile_argument in --profile -p; do
		run_codex "$profile_argument" custom
		[ "${lines[0]}" = "argv: $(launcher_arguments) <$profile_argument> <custom>" ]
	done
}

@test "passes caller arguments through after every injected argument" {
	run_codex resume --last
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive> <resume> <--last>" ]
}

@test "treats a leading flag as an interactive launch" {
	run_codex --search
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive> <--search>" ]
}

@test "treats fork as an interactive launch" {
	run_codex fork
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive> <fork>" ]
}

@test "treats a positional prompt as a private interactive launch" {
	run_codex 'explain this code'
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive> <explain this code>" ]
}

@test "keeps native management commands outside the interactive launch" {
	for command in plugin doctor queue; do
		run_codex "$command" --help
		[ "$status" -eq 0 ]
		[ "${lines[0]}" = "argv: $(launcher_arguments) <$command> <--help>" ]
	done
}

@test "leaves a subcommand launch without interactive preferences or profile activation" {
	run_codex exec "do the thing"
	[ "${lines[0]}" = "argv: $(launcher_arguments) <exec> <do the thing>" ]
	[ "${lines[1]}" = 'AGENT_INTERACTIVE_PREFERENCES_PATH=<unset>' ]
	[ ! -f "$DISPATCH_MARKER" ]
}

@test "preserves caller arguments that contain spaces and quotes" {
	run_codex exec 'a "quoted" argument'
	[ "${lines[0]}" = "argv: $(launcher_arguments) <exec> <a \"quoted\" argument>" ]
}

@test "keeps hook discovery overrides out of the interactive launch" {
	write_dispatch_file 'codexInteractiveProfile=dotfiles-workspace-test' \
		"workspaceProfileArguments+=(-c 'model_reasoning_effort=\"high\"')"
	run_codex -C '/a project' resume --last
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-workspace-test> <-C> </a project> <resume> <--last>" ]
	run cat "$HOOK_TRUST_ARGUMENTS_FILE"
	[ "$output" = $'<-c>\n<model_reasoning_effort="high">\n<-C>\n</a project>\n<resume>\n<--last>' ]
}

@test "does not mistake a positional prompt for an explicit profile flag" {
	run_codex -- --profile=custom
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive> <--> <--profile=custom>" ]
}

@test "does not repeat an explicit embedded mode flag" {
	run_codex --no-daemon
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive> <--no-daemon>" ]
	run_codex --no-daemon --profile custom
	[ "${lines[0]}" = "argv: $(launcher_arguments) <--no-daemon> <--profile> <custom>" ]
}

@test "does not start codex when hook approval fails" {
	HOOK_TRUST_EXIT_STATUS=7
	run_codex
	[ "$status" -eq 7 ]
	[ -z "$output" ]
}

@test "explicit endpoints and informational options bypass automatic private server selection" {
	for argument in --no-daemon '--remote=unix:///custom.sock' --help --version; do
		run_codex "$argument"
		[ "$status" -eq 0 ]
		[ ! -f "$PRIVATE_LAUNCH_MARKER" ]
		[ "${lines[0]}" = "argv: $(launcher_arguments) <--profile> <dotfiles-interactive> <$argument>" ]
	done
}
