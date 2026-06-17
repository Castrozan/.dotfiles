# shellcheck shell=bash

_find_tmux_socket() {
	local uid
	uid="$(id -u)"
	find "/run/user/${uid}/tmux-${uid}" "/tmp/tmux-${uid}" -name default -type s 2>/dev/null | head -1 || true
}

_resolve_tmux_target_from_specifier() {
	local target_specifier="$1"
	local tmux_socket="$2"

	if echo "$target_specifier" | grep -q ':'; then
		echo "$target_specifier"
		return
	fi

	local current_session
	current_session="$(tmux -S "$tmux_socket" display-message -p '#S' 2>/dev/null || echo "")"
	if [[ -z "$current_session" ]]; then
		echo >&2 "Error: no session in target specifier and not inside tmux"
		exit 1
	fi

	echo "${current_session}:${target_specifier}"
}

_create_tmux_window_at_target() {
	local session="$1"
	local window_name="$2"
	local working_directory="$3"
	local tmux_socket="$4"

	tmux -S "$tmux_socket" new-window -t "$session" -n "$window_name" -c "$working_directory"
	tmux -S "$tmux_socket" list-windows -t "$session" | grep -q "$window_name" || {
		echo >&2 "Error: failed to create window '${window_name}' in session '${session}'"
		exit 1
	}
}

_build_claude_invocation_with_instructions_file() {
	local instructions_file="$1"
	local model="${2:-}"

	local model_flag=""
	if [[ -n "$model" ]]; then
		model_flag="--model $model"
	fi

	echo "claude ${model_flag} \"Read the task at ${instructions_file} and implement it. Work autonomously.\""
}

_send_command_to_tmux_pane() {
	local target_window="$1"
	local command_to_run="$2"
	local tmux_socket="$3"

	local pane_index
	pane_index="$(tmux -S "$tmux_socket" list-panes -t "$target_window" -F "#{pane_index}" | head -1)"

	tmux -S "$tmux_socket" send-keys -t "${target_window}.${pane_index}" "$command_to_run" Enter
}
