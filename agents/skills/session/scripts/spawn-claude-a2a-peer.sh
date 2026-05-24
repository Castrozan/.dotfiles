# shellcheck shell=bash

readonly A2A_PORT_PICK_LOCK_DIRECTORY="/tmp/spawn-claude-a2a-port-pick.lock"
readonly A2A_PORT_PICK_LOCK_ACQUIRE_TIMEOUT_SECONDS=15
readonly A2A_PEER_BIND_OBSERVATION_TIMEOUT_SECONDS=10

_acquire_a2a_port_pick_lock_or_exit() {
	local elapsed_tenths_of_seconds=0
	while ! mkdir "$A2A_PORT_PICK_LOCK_DIRECTORY" 2>/dev/null; do
		if ((elapsed_tenths_of_seconds >= A2A_PORT_PICK_LOCK_ACQUIRE_TIMEOUT_SECONDS * 10)); then
			echo >&2 "Error: could not acquire ${A2A_PORT_PICK_LOCK_DIRECTORY} within ${A2A_PORT_PICK_LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
			exit 1
		fi
		sleep 0.1
		elapsed_tenths_of_seconds=$((elapsed_tenths_of_seconds + 1))
	done
}

_release_a2a_port_pick_lock() {
	rmdir "$A2A_PORT_PICK_LOCK_DIRECTORY" 2>/dev/null || true
}

_is_tcp_port_listening_on_loopback() {
	local port="$1"
	(exec 3<>"/dev/tcp/127.0.0.1/${port}") 2>/dev/null
	local connect_exit_code=$?
	exec 3>&- 2>/dev/null || true
	return $connect_exit_code
}

_pick_free_tcp_port_in_a2a_range() {
	local port
	for port in $(seq "$A2A_PORT_RANGE_START" "$A2A_PORT_RANGE_END"); do
		if ! _is_tcp_port_listening_on_loopback "$port"; then
			echo "$port"
			return
		fi
	done
	echo >&2 "Error: no free TCP port found in range ${A2A_PORT_RANGE_START}-${A2A_PORT_RANGE_END}"
	exit 1
}

_wait_until_port_is_listening_or_timeout() {
	local port="$1"
	local elapsed_tenths_of_seconds=0
	while ! _is_tcp_port_listening_on_loopback "$port"; do
		if ((elapsed_tenths_of_seconds >= A2A_PEER_BIND_OBSERVATION_TIMEOUT_SECONDS * 10)); then
			return 1
		fi
		sleep 0.1
		elapsed_tenths_of_seconds=$((elapsed_tenths_of_seconds + 1))
	done
}

_spawn_a2a_peer_window_for_agent() {
	local session="$1"
	local agent_window_name="$2"
	local working_directory="$3"
	local agent_name="$4"
	local listen_port="$5"
	local meaningful_line_pattern="$6"
	local tmux_socket="$7"

	local peer_window_name="${agent_window_name}-a2a"
	_create_tmux_window_at_target "$session" "$peer_window_name" "$working_directory" "$tmux_socket"

	local peer_command
	peer_command="claude-a2a-peer --tmux-target ${session}:${agent_window_name} --name ${agent_name} --port ${listen_port} --pattern $(printf %q "$meaningful_line_pattern")"
	_send_command_to_tmux_pane "${session}:${peer_window_name}" "$peer_command" "$tmux_socket"

	if ! _wait_until_port_is_listening_or_timeout "$listen_port"; then
		echo >&2 "Warning: A2A peer did not bind ${listen_port} within ${A2A_PEER_BIND_OBSERVATION_TIMEOUT_SECONDS}s (look in tmux ${session}:${peer_window_name})"
	fi
}
