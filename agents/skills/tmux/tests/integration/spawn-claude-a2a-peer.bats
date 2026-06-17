#!/usr/bin/env bats

setup() {
	HELPER_SCRIPT_PATH="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../scripts/spawn-claude-a2a-peer.sh"
	A2A_PORT_RANGE_START=51200
	A2A_PORT_RANGE_END=51209
	# shellcheck disable=SC1090
	source "$HELPER_SCRIPT_PATH"
}

@test "script source has no lsof references (regression for PATH-missing false-success bug)" {
	run grep -c '\blsof\b' "$HELPER_SCRIPT_PATH"
	[ "$output" = "0" ]
}

@test "script source uses bash builtin /dev/tcp for port probing" {
	run grep -c '/dev/tcp/' "$HELPER_SCRIPT_PATH"
	[ "$output" -ge 1 ]
}

@test "_is_tcp_port_listening_on_loopback returns nonzero when nothing is bound to the port" {
	run _is_tcp_port_listening_on_loopback 1
	[ "$status" -ne 0 ]
}

@test "_is_tcp_port_listening_on_loopback returns zero when a server is bound to the port" {
	python3 -c "
import socket, time, sys
listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listening_socket.bind(('127.0.0.1', int(sys.argv[1])))
listening_socket.listen()
time.sleep(2)
" 51299 &
	background_server_pid=$!
	sleep 0.3
	run _is_tcp_port_listening_on_loopback 51299
	kill "$background_server_pid" 2>/dev/null || true
	wait "$background_server_pid" 2>/dev/null || true
	[ "$status" -eq 0 ]
}

@test "_pick_free_tcp_port_in_a2a_range returns a port inside the configured range" {
	run _pick_free_tcp_port_in_a2a_range
	[ "$status" -eq 0 ]
	[ "$output" -ge "$A2A_PORT_RANGE_START" ]
	[ "$output" -le "$A2A_PORT_RANGE_END" ]
}

@test "_pick_free_tcp_port_in_a2a_range exits nonzero when every port in range is listening" {
	listening_server_pids=()
	for port in $(seq "$A2A_PORT_RANGE_START" "$A2A_PORT_RANGE_END"); do
		python3 -c "
import socket, time, sys
listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listening_socket.bind(('127.0.0.1', int(sys.argv[1])))
listening_socket.listen()
time.sleep(5)
" "$port" &
		listening_server_pids+=($!)
	done
	sleep 0.5
	run _pick_free_tcp_port_in_a2a_range
	for pid in "${listening_server_pids[@]}"; do
		kill "$pid" 2>/dev/null || true
	done
	wait "${listening_server_pids[@]}" 2>/dev/null || true
	[ "$status" -ne 0 ]
}
