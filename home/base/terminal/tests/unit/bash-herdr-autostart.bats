#!/usr/bin/env bats

setup() {
	herdrAutostartScript="$BATS_TEST_DIRNAME/../../shell/bash_herdr_autostart.sh"
	workspaceStateFile="${BATS_TEST_TMPDIR:-$BATS_TMPDIR}/workspace-grid-state"
}

resolved_session_name_for_workspace() {
	local workspaceNumber="$1"
	local designatedDefaultSessionWorkspaceNumber="$2"
	printf '%s\n' "$workspaceNumber" >"$workspaceStateFile"
	HAMMERSPOON_WORKSPACE_STATE_FILE="$workspaceStateFile" \
		HERDR_DEFAULT_SESSION_WORKSPACE_NUMBER="$designatedDefaultSessionWorkspaceNumber" \
		bash -c "source '$herdrAutostartScript'; _current_workspace_herdr_session_name"
}

@test "the designated workspace resolves to the shared default session, emitting an empty name" {
	run resolved_session_name_for_workspace 4 4
	[ "$status" -eq 0 ]
	[ -z "$output" ]
}

@test "a non-designated workspace resolves to its own per-workspace session" {
	run resolved_session_name_for_workspace 3 4
	[ "$status" -eq 0 ]
	[ "$output" = "workspace-3" ]
}

@test "with no designated workspace even the number-4 workspace gets its own session" {
	run resolved_session_name_for_workspace 4 ""
	[ "$status" -eq 0 ]
	[ "$output" = "workspace-4" ]
}

@test "a missing workspace-state file resolves to the shared default session" {
	rm -f "$workspaceStateFile"
	run env \
		HAMMERSPOON_WORKSPACE_STATE_FILE="$workspaceStateFile" \
		HERDR_DEFAULT_SESSION_WORKSPACE_NUMBER=4 \
		bash -c "source '$herdrAutostartScript'; _current_workspace_herdr_session_name"
	[ "$status" -eq 0 ]
	[ -z "$output" ]
}

@test "a non-numeric workspace state resolves to the shared default session" {
	run resolved_session_name_for_workspace garbage 4
	[ "$status" -eq 0 ]
	[ -z "$output" ]
}
