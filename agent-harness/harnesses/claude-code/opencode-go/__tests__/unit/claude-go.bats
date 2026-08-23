#!/usr/bin/env bats

load '../../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/claude-go"
	WRAPPER_SHELL="$BASH"
	TEMPORARY_ROOT="$(mktemp -d)"
	FAKE_BINARY_DIRECTORY="$TEMPORARY_ROOT/bin"
	PROXY_LISTEN_ADDRESS="127.0.0.1"
	PROXY_LISTEN_PORT="1"
	PROXY_INSPECTION_COMMAND="launchctl print gui/@CURRENT_USER_ID@/com.dotfiles.claude-go-proxy"
	LISTENER_PROCESS_ID=""
	mkdir -p "$FAKE_BINARY_DIRECTORY"

	cat >"$FAKE_BINARY_DIRECTORY/claude" <<-'FAKE_CLAUDE'
		#!/usr/bin/env bash
		printf 'argv:'
		printf ' <%s>' "$@"
		printf '\n'
		printf 'ANTHROPIC_API_KEY=<%s>\n' "${ANTHROPIC_API_KEY-unset}"
		printf 'ANTHROPIC_BASE_URL=<%s>\n' "${ANTHROPIC_BASE_URL-unset}"
		printf 'ANTHROPIC_DEFAULT_OPUS_MODEL=<%s>\n' "${ANTHROPIC_DEFAULT_OPUS_MODEL-unset}"
	FAKE_CLAUDE

	chmod +x "$FAKE_BINARY_DIRECTORY/claude"
}

teardown() {
	if [ -n "$LISTENER_PROCESS_ID" ]; then
		kill "$LISTENER_PROCESS_ID" 2>/dev/null || true
		wait "$LISTENER_PROCESS_ID" 2>/dev/null || true
	fi
	rm -rf "$TEMPORARY_ROOT"
}

listen_on_a_free_loopback_port() {
	if ! command -v python3 &>/dev/null; then
		skip "python3 not installed"
	fi
	local portFile="$TEMPORARY_ROOT/listening-port"
	python3 -c '
import socket, sys, time
server = socket.socket()
server.bind(("127.0.0.1", 0))
server.listen(8)
with open(sys.argv[1], "w") as portFile:
    portFile.write(str(server.getsockname()[1]))
time.sleep(30)
' "$portFile" &
	LISTENER_PROCESS_ID=$!
	local waitedTenths=0
	while [ ! -s "$portFile" ] && [ "$waitedTenths" -lt 100 ]; do
		sleep 0.1
		waitedTenths=$((waitedTenths + 1))
	done
	[ -s "$portFile" ]
	PROXY_LISTEN_PORT="$(cat "$portFile")"
}

run_claude_go() {
	run env -i \
		PATH="$FAKE_BINARY_DIRECTORY:$PATH" \
		ANTHROPIC_API_KEY="a-plan-key-that-must-not-travel" \
		ANTHROPIC_BASE_URL="http://$PROXY_LISTEN_ADDRESS:$PROXY_LISTEN_PORT" \
		ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro" \
		CLAUDE_GO_LAUNCHER_PROXY_LISTEN_ADDRESS="$PROXY_LISTEN_ADDRESS" \
		CLAUDE_GO_LAUNCHER_PROXY_LISTEN_PORT="$PROXY_LISTEN_PORT" \
		CLAUDE_GO_LAUNCHER_PROXY_INSPECTION_COMMAND="$PROXY_INSPECTION_COMMAND" \
		CLAUDE_GO_LAUNCHER_CLAUDE_BINARY="$FAKE_BINARY_DIRECTORY/claude" \
		CLAUDE_GO_LAUNCHER_MODEL="deepseek-v4-flash" \
		"$WRAPPER_SHELL" "$SCRIPT_UNDER_TEST" "$@"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "starts claude on the pinned model when given no arguments" {
	run_claude_go
	[ "$status" -eq 0 ]
	[[ "$output" == *'argv: <--model> <deepseek-v4-flash>'* ]]
}

@test "passes caller arguments through after the pinned model" {
	run_claude_go --resume "a prompt"
	[[ "$output" == *'argv: <--model> <deepseek-v4-flash> <--resume> <a prompt>'* ]]
}

@test "removes the plan api key from the launched environment" {
	run_claude_go
	[[ "$output" == *'ANTHROPIC_API_KEY=<unset>'* ]]
}

@test "hands the proxy environment the wrapper exported to claude" {
	run_claude_go
	[[ "$output" == *"ANTHROPIC_BASE_URL=<http://$PROXY_LISTEN_ADDRESS:$PROXY_LISTEN_PORT>"* ]]
	[[ "$output" == *'ANTHROPIC_DEFAULT_OPUS_MODEL=<deepseek-v4-pro>'* ]]
}

@test "reports a proxy that is not listening and why it matters" {
	run_claude_go
	[[ "$output" == *"claude-go: the Console Go translation proxy is not listening on $PROXY_LISTEN_ADDRESS:$PROXY_LISTEN_PORT."* ]]
	[[ "$output" == *"Console Go's own Anthropic endpoint drops tool names"* ]]
}

@test "names the inspection command with the current user id resolved" {
	run_claude_go
	[[ "$output" == *"Inspect the service: launchctl print gui/$(id -u)/com.dotfiles.claude-go-proxy"* ]]
	[[ "$output" != *'@CURRENT_USER_ID@'* ]]
}

@test "starts claude even when the proxy is down" {
	run_claude_go
	[ "$status" -eq 0 ]
	[[ "$output" == *'argv: <--model> <deepseek-v4-flash>'* ]]
}

@test "stays quiet when the proxy is listening" {
	listen_on_a_free_loopback_port
	run_claude_go
	[ "$status" -eq 0 ]
	[[ "$output" != *'is not listening'* ]]
	[[ "$output" == *'argv: <--model> <deepseek-v4-flash>'* ]]
}
