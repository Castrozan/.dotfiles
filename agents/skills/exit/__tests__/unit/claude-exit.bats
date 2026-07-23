#!/usr/bin/env bats

load '../../../../../__tests__/helpers/bash-script-assertions'

setup() {
	stubbedProcessTreeDirectory="$(mktemp -d)"
	cat >"$stubbedProcessTreeDirectory/ps" <<'STUB'
#!/usr/bin/env bash
requestedProcessId="$2"
requestedField="$4"
case "$requestedProcessId" in
2100) commandPath="/usr/local/bin/bash"; parentProcessId="2200" ;;
2200) commandPath="/run/current-system/sw/bin/fish"; parentProcessId="2300" ;;
2300) commandPath="/nix/store/abc-claude-code-unwrapped/bin/claude"; parentProcessId="2400" ;;
2400) commandPath="tmux"; parentProcessId="1" ;;
9100) commandPath="/usr/local/bin/bash"; parentProcessId="9200" ;;
9200) commandPath="/run/current-system/sw/bin/fish"; parentProcessId="9300" ;;
9300) commandPath="tmux"; parentProcessId="1" ;;
*) exit 1 ;;
esac
case "$requestedField" in
comm=) printf '%s\n' "$commandPath" ;;
ppid=) printf '%s\n' "$parentProcessId" ;;
esac
STUB
	chmod +x "$stubbedProcessTreeDirectory/ps"
	exitScriptsDirectory="$DOTFILES_SKILLS_DIRECTORY/exit/scripts"
}

teardown() {
	rm -rf "$stubbedProcessTreeDirectory"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "validates process name before killing" {
	assert_script_source_matches 'Safety check'
}

@test "uses SIGTERM for clean shutdown" {
	assert_script_source_matches "SIGTERM"
}

@test "delegates to find-claude-ancestor-pid and reports the target without killing" {
	PATH="$stubbedProcessTreeDirectory:$exitScriptsDirectory:$PATH" \
		CLAUDE_EXIT_ANCESTOR_SCAN_START_PROCESS_ID=2100 \
		run_script_under_test --print-target
	[ "$status" -eq 0 ]
	[[ "$output" == *"Claude PID: 2300"* ]]
}

@test "fails safe when no claude process is in the ancestor chain" {
	PATH="$stubbedProcessTreeDirectory:$exitScriptsDirectory:$PATH" \
		CLAUDE_EXIT_ANCESTOR_SCAN_START_PROCESS_ID=9100 \
		run_script_under_test --print-target
	[ "$status" -ne 0 ]
	[[ "$output" == *"Safety check FAILED"* ]]
}
