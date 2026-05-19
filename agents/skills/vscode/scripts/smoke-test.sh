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

run_step "command-by-title returns ok:true JSON" assert_substring_in_command_output '"ok": true' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" command-by-title "Preferences: Open Settings (UI)"

run_step "dismiss-modals rejects non-integer" \
	bash -c '"$0" --port "$1" dismiss-modals foo 2>&1 | grep -q "must be a positive integer"' \
	"$VSCODE_CLI" "$TEST_CDP_PORT"
echo "ok: non-integer rejected"

run_step "dismiss-modals accepts integer" assert_substring_in_command_output '"presses": 2' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" dismiss-modals 2

run_step "open Claude Code chat panel" assert_substring_in_command_output '"ok": true' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" command-by-title "Chat: Focus on Chat View"
sleep 2

run_step "probe-chat-dom reports pinned chat input + send selectors as found" \
	bash -c '
		probe_output=$("$0" --port "$1" probe-chat-dom 2>&1)
		input_found=$(printf %s "$probe_output" | jq -r ".pinned_selectors.chat_input_editor.found // false")
		send_found=$(printf %s "$probe_output" | jq -r ".pinned_selectors.send_button.found // false")
		if [ "$input_found" != "true" ] || [ "$send_found" != "true" ]; then
			echo "FAIL: pinned selectors not found in live DOM" >&2
			echo "  chat_input_editor.found = $input_found" >&2
			echo "  send_button.found       = $send_found" >&2
			echo "  (selectors may have drifted — diff full probe-chat-dom output against docs/CDP-SELECTORS.md)" >&2
			exit 1
		fi
		echo "ok: chat_input_editor + send_button both found"
	' "$VSCODE_CLI" "$TEST_CDP_PORT"

run_step "agent state returns running boolean" assert_substring_in_command_output '"running"' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" agent state

run_step "agent read returns last_assistant_text key" assert_substring_in_command_output '"last_assistant_text"' \
	"$VSCODE_CLI" --port "$TEST_CDP_PORT" agent read

# The end-to-end `agent send` round-trip POSTS a real message into the user's
# Claude Code chat history, consuming API tokens and leaving a transcript
# entry every smoke run. Gated behind an opt-in env var so the default
# `./smoke-test.sh` invocation stays side-effect-free.
if [ "${VSCODE_SKILL_SMOKE_SIDE_EFFECTS:-0}" = "1" ]; then
	run_step "agent send returns ok:true (sends a tiny prompt to the real chat)" \
		assert_substring_in_command_output '"ok": true' \
		"$VSCODE_CLI" --port "$TEST_CDP_PORT" agent send "Reply with just OK."
	# Give the chat engine ~3 s to ack the send before snapshotting state.
	sleep 3
	run_step "agent state observes the in-flight turn (running=true OR messages>0)" \
		bash -c '
			state=$("$0" --port "$1" agent state 2>&1)
			if printf %s "$state" | grep -qE "\"running\":[[:space:]]*true|\"assistant_messages\":[[:space:]]*[1-9]"; then
				echo "ok: send round-trip received by chat"
			else
				echo "FAIL: send was accepted but chat never registered a turn"
				echo "agent state output: $state"
				exit 1
			fi
		' "$VSCODE_CLI" "$TEST_CDP_PORT"
else
	echo ""
	echo "=== agent send round-trip (skipped) ==="
	echo "skipped: set VSCODE_SKILL_SMOKE_SIDE_EFFECTS=1 to enable. The opt-in step posts a real prompt to the user's Claude Code session and consumes API tokens."
fi

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
