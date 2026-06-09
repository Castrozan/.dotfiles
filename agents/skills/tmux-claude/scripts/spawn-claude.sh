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

_build_claude_command() {
	local model="$1"
	local skip_permissions="$2"
	local claude_display_name="$3"

	local command_parts="claude"

	if [[ -n "$model" ]]; then
		command_parts+=" --model ${model}"
	fi

	if [[ "$skip_permissions" == "true" ]]; then
		command_parts+=" --dangerously-skip-permissions"
	fi

	if [[ -n "$claude_display_name" ]]; then
		command_parts+=" --name ${claude_display_name}"
	fi

	echo "$command_parts"
}

_send_command_to_tmux_pane() {
	local target_window="$1"
	local command_to_run="$2"
	local tmux_socket="$3"

	local pane_index
	pane_index="$(tmux -S "$tmux_socket" list-panes -t "$target_window" -F "#{pane_index}" | head -1)"

	tmux -S "$tmux_socket" send-keys -t "${target_window}.${pane_index}" "$command_to_run" Enter
}

_wait_for_claude_input_prompt() {
	local target_window="$1"
	local tmux_socket="$2"
	local max_attempts=20

	for ((attempt = 1; attempt <= max_attempts; attempt++)); do
		local pane_content
		pane_content="$(tmux -S "$tmux_socket" capture-pane -t "$target_window" -p -S -10 2>/dev/null || echo "")"
		if echo "$pane_content" | grep -q '❯'; then
			return 0
		fi
		sleep 1
	done

	echo >&2 "Warning: claude input prompt not detected after ${max_attempts}s, sending prompt anyway"
	return 0
}

_send_initial_prompt_to_claude() {
	local target_window="$1"
	local tmux_socket="$2"
	local prompt_text="$3"
	local prompt_file="$4"

	_wait_for_claude_input_prompt "$target_window" "$tmux_socket"

	if [[ -n "$prompt_file" ]]; then
		_send_command_to_tmux_pane "$target_window" "Read the task at ${prompt_file} and implement it." "$tmux_socket"
	elif [[ -n "$prompt_text" ]]; then
		_send_command_to_tmux_pane "$target_window" "$prompt_text" "$tmux_socket"
	fi
}

_print_help_and_exit() {
	cat <<EOF
Usage: ${SCRIPT_NAME} <target> <working-dir> [options]

Launch a Claude Code session in a tmux window.

Arguments:
  target             tmux target: "session:window-name" or just "window-name" (uses current session)
  working-dir        directory to start in

Options:
  --prompt TEXT       send an initial prompt after claude starts
  --file PATH        send "Read the task at PATH and implement it." as the initial prompt
  --model MODEL      claude model to use (default: inherits from config)
  --skip-permissions  run with --dangerously-skip-permissions
  --name NAME        set a display name for the claude session

Examples:
  ${SCRIPT_NAME} dotfiles:refactor ~/projects/app
  ${SCRIPT_NAME} feature-work ~/projects/app --prompt "Fix the login bug in auth.ts"
  ${SCRIPT_NAME} task-agent ~/projects/app --file /tmp/task.md --skip-permissions
  ${SCRIPT_NAME} review ~/projects/app --model sonnet --name "code-review"
EOF
	exit 0
}

_print_usage_error_and_exit() {
	echo >&2 "Error: missing required arguments. Run '${SCRIPT_NAME} --help' for usage."
	exit 1
}

main() {
	if [[ $# -lt 2 ]]; then
		if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
			_print_help_and_exit
		fi
		_print_usage_error_and_exit
	fi

	local target_specifier="$1"
	local working_directory="$2"
	local model=""
	local skip_permissions="false"
	local claude_display_name=""
	local prompt_text=""
	local prompt_file=""

	shift 2
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--model)
			model="$2"
			shift 2
			;;
		--skip-permissions)
			skip_permissions="true"
			shift
			;;
		--name)
			claude_display_name="$2"
			shift 2
			;;
		--prompt)
			prompt_text="$2"
			shift 2
			;;
		--file)
			prompt_file="$2"
			shift 2
			;;
		--help | -h)
			_print_help_and_exit
			;;
		*)
			echo >&2 "Error: unknown option: $1"
			_print_usage_error_and_exit
			;;
		esac
	done

	if [[ -n "$prompt_text" && -n "$prompt_file" ]]; then
		echo >&2 "Error: --prompt and --file are mutually exclusive"
		exit 1
	fi

	if [[ -n "$prompt_file" && ! -f "$prompt_file" ]]; then
		echo >&2 "Error: prompt file not found: ${prompt_file}"
		exit 1
	fi

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
	claude_command="$(_build_claude_command "$model" "$skip_permissions" "$claude_display_name")"

	_send_command_to_tmux_pane "${session}:${window_name}" "$claude_command" "$tmux_socket"

	if [[ -n "$prompt_text" || -n "$prompt_file" ]]; then
		_send_initial_prompt_to_claude "${session}:${window_name}" "$tmux_socket" "$prompt_text" "$prompt_file"
	fi

	echo "Spawned claude in ${session}:${window_name}"
}

main "$@"
