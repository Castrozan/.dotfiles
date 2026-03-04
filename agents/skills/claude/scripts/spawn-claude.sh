#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_NAME="spawn-claude"

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

_print_usage_and_exit() {
	cat >&2 <<EOF
Usage: ${SCRIPT_NAME} <target> <working-dir> <instructions-file> [--model MODEL]

  target             tmux target: "session:window-name" or just "window-name" (uses current session)
  working-dir        directory to cd into before starting claude
  instructions-file  path to file containing task instructions for the spawned agent

  --model MODEL      claude model to use (optional, uses default if omitted)

Examples:
  ${SCRIPT_NAME} dotfiles:task-resume ~/.dotfiles /tmp/task.md
  ${SCRIPT_NAME} feature-work ~/projects/app /tmp/instructions.md --model claude-sonnet-4-6
EOF
	exit 1
}

main() {
	if [[ $# -lt 3 ]]; then
		_print_usage_and_exit
	fi

	local target_specifier="$1"
	local working_directory="$2"
	local instructions_file="$3"
	local model=""

	shift 3
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--model)
			model="$2"
			shift 2
			;;
		*)
			echo >&2 "Unknown option: $1"
			_print_usage_and_exit
			;;
		esac
	done

	[[ -f "$instructions_file" ]] || {
		echo >&2 "Error: instructions file not found: ${instructions_file}"
		exit 1
	}

	[[ -d "$working_directory" ]] || {
		echo >&2 "Error: working directory not found: ${working_directory}"
		exit 1
	}

	local tmux_socket
	tmux_socket="$(_find_tmux_socket)"
	[[ -n "$tmux_socket" ]] || {
		echo >&2 "Error: no tmux socket found"
		exit 1
	}

	local resolved_target
	resolved_target="$(_resolve_tmux_target_from_specifier "$target_specifier" "$tmux_socket")"

	local session window_name
	session="${resolved_target%%:*}"
	window_name="${resolved_target##*:}"

	_create_tmux_window_at_target "$session" "$window_name" "$working_directory" "$tmux_socket"

	local claude_command
	claude_command="$(_build_claude_invocation_with_instructions_file "$instructions_file" "$model")"

	_send_command_to_tmux_pane "${session}:${window_name}" "$claude_command" "$tmux_socket"

	echo "Spawned claude in ${session}:${window_name} — working from ${instructions_file}"
}

main "$@"
