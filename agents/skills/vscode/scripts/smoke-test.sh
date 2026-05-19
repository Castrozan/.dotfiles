#!/usr/bin/env bash
# Smoke test for the vscode CDP skill. Walks the full lifecycle and fails fast
# on any deviation. Uses port 9333 because the Nix-wrapped `code` binary
# (~/.dotfiles/home/modules/editor/vscode/vscode.nix) hard-codes that port via
# wrapProgram; launching on any other port would not bind. This test will
# CLOSE any running VS Code on 9333 at start — close unsaved buffers first or
# expect the quit-confirmation dialog to swallow keyboard input until handled.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly SCRIPT_DIR
readonly VSCODE_CLI="${SCRIPT_DIR}/vscode"
readonly TEST_CDP_PORT=9333
readonly SCREENSHOT_OUTPUT_PATH="/tmp/vscode-cdp-smoke-test.png"

run_step() {
	local step_label="$1"
	shift
	printf '\n=== %s ===\n' "$step_label"
	"$@"
}

assert_substring_in_command_output() {
	local expected_substring="$1"
	shift
	local actual_output
	# The command under test is allowed to exit non-zero (e.g. an
	# unimplemented agent subverb exits 1 by design). With `set -e` an
	# assignment that captures a non-zero command-substitution exit would
	# abort the whole test, so we explicitly mask it here.
	actual_output="$("$@" 2>&1)" || true
	if [[ "$actual_output" != *"$expected_substring"* ]]; then
		printf 'FAIL: expected output to contain %q\nActual output:\n%s\n' "$expected_substring" "$actual_output" >&2
		exit 1
	fi
	printf 'ok: %q found in output of %s\n' "$expected_substring" "$*"
}

assert_file_is_png() {
	local png_path="$1"
	if [[ ! -s "$png_path" ]]; then
		echo "FAIL: $png_path is missing or empty" >&2
		exit 1
	fi
	if ! file "$png_path" | grep -q 'PNG image'; then
		echo "FAIL: $png_path is not a PNG (file: $(file "$png_path"))" >&2
		exit 1
	fi
	echo "ok: $png_path is a PNG"
}

cleanup_on_exit() {
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" kill >/dev/null 2>&1 || true
	rm -f "$SCREENSHOT_OUTPUT_PATH"
}
trap cleanup_on_exit EXIT

run_step "launch (clean)" "$VSCODE_CLI" --port "$TEST_CDP_PORT" kill
run_step "launch" "$VSCODE_CLI" --port "$TEST_CDP_PORT" launch
sleep 5

run_step "status reports Running" assert_substring_in_command_output "Running:" \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" status

run_step "cdp-pages lists at least one renderer page" assert_substring_in_command_output "[page]" \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" cdp-pages

run_step "cdp-pages --raw returns JSON array" assert_substring_in_command_output "webSocketDebuggerUrl" \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" cdp-pages --raw

run_step "screenshot writes a PNG file" "$VSCODE_CLI" --port "$TEST_CDP_PORT" \
	screenshot --out "$SCREENSHOT_OUTPUT_PATH"
assert_file_is_png "$SCREENSHOT_OUTPUT_PATH"

run_step "run-command returns ok:true JSON" assert_substring_in_command_output '"ok": true' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" run-command "Preferences: Open Settings (UI)"

run_step "dismiss-modals rejects non-integer" \
	bash -c '"$0" --port "$1" dismiss-modals foo 2>&1 | grep -q "must be a positive integer"' \
	"$VSCODE_CLI" "$TEST_CDP_PORT"
echo "ok: non-integer rejected"

run_step "dismiss-modals accepts integer" assert_substring_in_command_output '"presses": 2' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" dismiss-modals 2

run_step "open Claude Code chat panel" assert_substring_in_command_output '"ok": true' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" run-command "workbench.action.chat.openInSidebar"
sleep 2

run_step "probe-chat-dom resolves pinned chat input selector" assert_substring_in_command_output '"chat_input_editor"' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" probe-chat-dom

run_step "agent state returns ok:true JSON" assert_substring_in_command_output '"ok": true' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" agent state

run_step "agent read returns ok:true JSON" assert_substring_in_command_output '"ok": true' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" agent read

run_step "unimplemented agent subverb returns clear stub error" assert_substring_in_command_output "not implemented yet" \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" agent history

run_step "unknown agent subverb is rejected" \
	bash -c '"$0" --port "$1" agent bogus 2>&1 | grep -q "Unknown agent subverb"' \
	"$VSCODE_CLI" "$TEST_CDP_PORT"
echo "ok: unknown agent subverb rejected"

run_step "snapshot returns non-trivial JSON" bash -c '
	output_size=$("$0" --port "$1" snapshot | wc -c)
	if [ "$output_size" -lt 1000 ]; then
		echo "FAIL: snapshot output suspiciously small ($output_size bytes)" >&2
		exit 1
	fi
	echo "ok: snapshot returned $output_size bytes"
' "$VSCODE_CLI" "$TEST_CDP_PORT"

run_step "kill" "$VSCODE_CLI" --port "$TEST_CDP_PORT" kill

printf '\n=== SMOKE TEST PASSED ===\n'
