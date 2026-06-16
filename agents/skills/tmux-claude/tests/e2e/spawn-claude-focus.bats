#!/usr/bin/env bats

setup() {
	local script_directory
	script_directory="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../scripts"

	STUB_BIN_DIR="${BATS_TEST_TMPDIR}/stub-bin"
	mkdir -p "$STUB_BIN_DIR"
	cat >"$STUB_BIN_DIR/claude" <<'STUB'
#!/usr/bin/env bash
printf '\n  ❯ \n'
exec sleep 60
STUB
	chmod +x "$STUB_BIN_DIR/claude"
	export PATH="$STUB_BIN_DIR:$PATH"

	TEST_TMUX_SOCKET="${BATS_TEST_TMPDIR}/tmux-test.sock"
	tmux -S "$TEST_TMUX_SOCKET" new-session -d -s viewer -n anchor -c "$BATS_TEST_TMPDIR"
	tmux -S "$TEST_TMUX_SOCKET" new-window -d -t viewer -n sibling -c "$BATS_TEST_TMPDIR"
	tmux -S "$TEST_TMUX_SOCKET" select-window -t viewer:anchor

	# shellcheck disable=SC1091
	source "$script_directory/tmux-helpers.sh"
	# shellcheck disable=SC1090
	source "$script_directory/spawn-claude.sh"
	eval "_find_tmux_socket() { echo '$TEST_TMUX_SOCKET'; }"
}

teardown() {
	tmux -S "$TEST_TMUX_SOCKET" kill-server 2>/dev/null || true
}

_active_window_name() {
	tmux -S "$TEST_TMUX_SOCKET" display-message -p -t viewer "#{window_name}"
}

@test "spawn-claude adds a background window without moving the active window" {
	run main viewer:probe "$BATS_TEST_TMPDIR" --skip-permissions --name probe
	[ "$status" -eq 0 ]

	run tmux -S "$TEST_TMUX_SOCKET" list-windows -t viewer -F "#{window_name}"
	[[ "$output" == *probe* ]]

	run _active_window_name
	[ "$output" = "anchor" ]
}

@test "spawn-claude actually launches claude in the new window" {
	run main viewer:probe "$BATS_TEST_TMPDIR" --skip-permissions --name probe
	[ "$status" -eq 0 ]

	local pane_content=""
	for _attempt in $(seq 1 20); do
		pane_content="$(tmux -S "$TEST_TMUX_SOCKET" capture-pane -t viewer:probe -p 2>/dev/null || echo "")"
		[[ "$pane_content" == *"❯"* ]] && break
		sleep 0.3
	done
	[[ "$pane_content" == *"❯"* ]]
}

@test "the user's spawn loop never steals focus across many windows" {
	for window_number in 1 2 3 4 5 6; do
		run main "viewer:t-AP-${window_number}" "$BATS_TEST_TMPDIR" --skip-permissions --name "t-AP-${window_number}"
		[ "$status" -eq 0 ]
		run _active_window_name
		[ "$output" = "anchor" ]
	done

	run tmux -S "$TEST_TMUX_SOCKET" list-windows -t viewer -F "#{window_active} #{window_name}"
	[[ "$output" == *"1 anchor"* ]]
	[[ "$output" == *"0 t-AP-6"* ]]
}
