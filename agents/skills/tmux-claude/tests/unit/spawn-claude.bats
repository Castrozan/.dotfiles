#!/usr/bin/env bats

setup() {
	HELPER_SCRIPT_PATH="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../scripts/tmux-helpers.sh"
	# shellcheck disable=SC1090
	source "$HELPER_SCRIPT_PATH"
	TEST_TMUX_SOCKET="${BATS_TEST_TMPDIR}/tmux-test.sock"
}

teardown() {
	tmux -S "$TEST_TMUX_SOCKET" kill-server 2>/dev/null || true
}

@test "helper carries a session-creation branch so absent sessions are created" {
	run grep -c 'new-session' "$HELPER_SCRIPT_PATH"
	[ "$output" -ge 1 ]
}

@test "_ensure_tmux_session_and_window creates the session when it is absent" {
	run _ensure_tmux_session_and_window fresh-session first-window /tmp "$TEST_TMUX_SOCKET"
	[ "$status" -eq 0 ]

	run tmux -S "$TEST_TMUX_SOCKET" has-session -t fresh-session
	[ "$status" -eq 0 ]

	run tmux -S "$TEST_TMUX_SOCKET" list-windows -t fresh-session -F "#{window_name}"
	[[ "$output" == *first-window* ]]
}

@test "_ensure_tmux_session_and_window adds a window to an existing session" {
	tmux -S "$TEST_TMUX_SOCKET" new-session -d -s existing-session -n placeholder

	run _ensure_tmux_session_and_window existing-session added-window /tmp "$TEST_TMUX_SOCKET"
	[ "$status" -eq 0 ]

	run tmux -S "$TEST_TMUX_SOCKET" list-windows -t existing-session -F "#{window_name}"
	[[ "$output" == *placeholder* ]]
	[[ "$output" == *added-window* ]]
}
