#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

load '../support/codex_launcher_fixture'

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

@test "native launches do not inherit another interactive server socket" {
	for argument in exec --no-daemon '--remote=unix:///custom.sock'; do
		run_codex "$argument"
		[ "$status" -eq 0 ]
		[ "${lines[3]}" = 'CODEX_SESSION_SOCKET_PATH=<unset>' ]
	done
}
