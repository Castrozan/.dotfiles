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

@test "prints the claude pid when claude is the immediate parent" {
	PATH="$stubbedProcessTreeDirectory:$PATH" run_script_under_test 2300
	[ "$status" -eq 0 ]
	[ "$output" = "2300" ]
}

@test "walks past intermediate shells to the claude ancestor" {
	PATH="$stubbedProcessTreeDirectory:$PATH" run_script_under_test 2100
	[ "$status" -eq 0 ]
	[ "$output" = "2300" ]
}

@test "exits non-zero when no claude ancestor exists" {
	PATH="$stubbedProcessTreeDirectory:$PATH" run_script_under_test 9100
	[ "$status" -ne 0 ]
	[ -z "$output" ]
}
