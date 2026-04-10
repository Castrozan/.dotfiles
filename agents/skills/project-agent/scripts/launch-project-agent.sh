#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_NAME="launch-project-agent"
readonly DEFAULT_HEARTBEAT_INTERVAL="3,33 * * * *"
readonly DEFAULT_MODEL="opus"

_find_tmux_socket() {
	local uid
	uid="$(id -u)"
	find "/run/user/${uid}/tmux-${uid}" "/tmp/tmux-${uid}" -name default -type s 2>/dev/null | head -1 || true
}

_resolve_tmux_session_from_environment() {
	local tmux_socket="$1"
	tmux -S "$tmux_socket" display-message -p '#S' 2>/dev/null || echo ""
}

_validate_project_directory() {
	local project_directory="$1"

	if [[ ! -d "$project_directory" ]]; then
		echo >&2 "Error: project directory not found: ${project_directory}"
		exit 1
	fi

	if [[ ! -f "${project_directory}/CLAUDE.md" ]]; then
		echo >&2 "Error: no CLAUDE.md found in ${project_directory} - the agent needs instructions"
		exit 1
	fi
}

_ensure_heartbeat_file_exists() {
	local project_directory="$1"
	local heartbeat_file="${project_directory}/HEARTBEAT.md"

	if [[ ! -f "$heartbeat_file" ]]; then
		printf '# Heartbeat\n\nNo active work.\n' >"$heartbeat_file"
		echo "Created ${heartbeat_file}"
	fi
}

_derive_agent_name_from_project_directory() {
	local project_directory="$1"
	basename "$project_directory"
}

_build_claude_launch_command() {
	local model="$1"
	local agent_name="$2"

	local command_parts="claude"
	command_parts+=" --model ${model}"
	command_parts+=" --name ${agent_name}"
	command_parts+=" --dangerously-skip-permissions"

	echo "$command_parts"
}

_create_tmux_window_for_project_agent() {
	local tmux_socket="$1"
	local tmux_session="$2"
	local window_name="$3"
	local project_directory="$4"

	if tmux -S "$tmux_socket" list-windows -t "$tmux_session" -F "#{window_name}" 2>/dev/null | grep -qx "$window_name"; then
		echo >&2 "Error: tmux window '${window_name}' already exists in session '${tmux_session}'"
		echo >&2 "Attach with: tmux attach -t ${tmux_session}:${window_name}"
		exit 1
	fi

	tmux -S "$tmux_socket" new-window -t "$tmux_session" -n "$window_name" -c "$project_directory"
}

_send_keys_to_tmux_pane() {
	local tmux_socket="$1"
	local target="$2"
	local keys="$3"

	local pane_index
	pane_index="$(tmux -S "$tmux_socket" list-panes -t "$target" -F "#{pane_index}" | head -1)"
	tmux -S "$tmux_socket" send-keys -t "${target}.${pane_index}" "$keys" Enter
}

_wait_for_claude_input_prompt() {
	local tmux_socket="$1"
	local target="$2"
	local max_attempts=30

	for ((attempt = 1; attempt <= max_attempts; attempt++)); do
		local pane_content
		pane_content="$(tmux -S "$tmux_socket" capture-pane -t "$target" -p -S -10 2>/dev/null || echo "")"
		if echo "$pane_content" | grep -q '❯'; then
			return 0
		fi
		sleep 1
	done

	echo >&2 "Warning: claude input prompt not detected after ${max_attempts}s, sending bootstrap anyway"
	return 0
}

_build_bootstrap_prompt() {
	local heartbeat_interval="$1"

	cat <<BOOTSTRAP
You are a persistent project agent. Read your CLAUDE.md for your identity and instructions. Read HEARTBEAT.md for pending work.

Set up your heartbeat loop now: use CronCreate with durable: true, cron: "${heartbeat_interval}", recurring: true, and this prompt:

"Heartbeat tick. Read HEARTBEAT.md. If there are pending tasks with elapsed intervals, work on the highest priority one. If nothing needs attention, do nothing - do not respond or log."

After setting up the heartbeat, read HEARTBEAT.md and act on any pending work. If nothing is pending, report your status and wait for instructions.
BOOTSTRAP
}

_send_bootstrap_prompt_via_file() {
	local tmux_socket="$1"
	local target="$2"
	local heartbeat_interval="$3"

	local bootstrap_file
	bootstrap_file="$(mktemp /tmp/project-agent-bootstrap.XXXXXX.md)"

	_build_bootstrap_prompt "$heartbeat_interval" >"$bootstrap_file"

	_wait_for_claude_input_prompt "$tmux_socket" "$target"

	tmux -S "$tmux_socket" load-buffer "$bootstrap_file"
	tmux -S "$tmux_socket" paste-buffer -t "$target"
	tmux -S "$tmux_socket" send-keys -t "$target" Enter

	rm -f "$bootstrap_file"
}

_print_help_and_exit() {
	cat <<EOF
Usage: ${SCRIPT_NAME} <project-directory> [options]

Launch a persistent project agent (Claude Code session with heartbeat loop) in a tmux window.

Arguments:
  project-directory    Path to the project. Must contain a CLAUDE.md file.

Options:
  --model MODEL        Claude model (default: ${DEFAULT_MODEL})
  --name NAME          Agent name / tmux window name (default: derived from directory name)
  --heartbeat CRON     Heartbeat cron expression (default: "${DEFAULT_HEARTBEAT_INTERVAL}")
  --session SESSION    tmux session to create the window in (default: current session)
  --no-bootstrap       Skip sending the bootstrap prompt

Examples:
  ${SCRIPT_NAME} ~/repo/ai-first-initiative
  ${SCRIPT_NAME} ~/repo/my-project --model sonnet --heartbeat "*/15 * * * *"
  ${SCRIPT_NAME} ~/repo/my-project --name my-pm --session work
EOF
	exit 0
}

main() {
	if [[ $# -lt 1 ]]; then
		if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
			_print_help_and_exit
		fi
		echo >&2 "Error: missing project directory. Run '${SCRIPT_NAME} --help' for usage."
		exit 1
	fi

	if [[ "$1" == "--help" || "$1" == "-h" ]]; then
		_print_help_and_exit
	fi

	local project_directory
	project_directory="$(realpath "$1")"
	local model="$DEFAULT_MODEL"
	local agent_name=""
	local heartbeat_interval="$DEFAULT_HEARTBEAT_INTERVAL"
	local tmux_session_override=""
	local send_bootstrap="true"

	shift
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--model)
			model="$2"
			shift 2
			;;
		--name)
			agent_name="$2"
			shift 2
			;;
		--heartbeat)
			heartbeat_interval="$2"
			shift 2
			;;
		--session)
			tmux_session_override="$2"
			shift 2
			;;
		--no-bootstrap)
			send_bootstrap="false"
			shift
			;;
		--help | -h)
			_print_help_and_exit
			;;
		*)
			echo >&2 "Error: unknown option: $1"
			exit 1
			;;
		esac
	done

	_validate_project_directory "$project_directory"
	_ensure_heartbeat_file_exists "$project_directory"

	if [[ -z "$agent_name" ]]; then
		agent_name="$(_derive_agent_name_from_project_directory "$project_directory")"
	fi

	local tmux_socket
	tmux_socket="$(_find_tmux_socket)"
	if [[ -z "$tmux_socket" ]]; then
		echo >&2 "Error: no tmux socket found"
		exit 1
	fi

	local tmux_session
	if [[ -n "$tmux_session_override" ]]; then
		tmux_session="$tmux_session_override"
	else
		tmux_session="$(_resolve_tmux_session_from_environment "$tmux_socket")"
		if [[ -z "$tmux_session" ]]; then
			echo >&2 "Error: not inside tmux and no --session specified"
			exit 1
		fi
	fi

	_create_tmux_window_for_project_agent "$tmux_socket" "$tmux_session" "$agent_name" "$project_directory"

	local target="${tmux_session}:${agent_name}"
	local claude_command
	claude_command="$(_build_claude_launch_command "$model" "$agent_name")"

	_send_keys_to_tmux_pane "$tmux_socket" "$target" "$claude_command"

	if [[ "$send_bootstrap" == "true" ]]; then
		_send_bootstrap_prompt_via_file "$tmux_socket" "$target" "$heartbeat_interval"
	fi

	echo "Launched project agent '${agent_name}' in ${target}"
	echo "  Project: ${project_directory}"
	echo "  Model: ${model}"
	echo "  Heartbeat: ${heartbeat_interval}"
	echo "  Attach: tmux select-window -t ${target}"
}

main "$@"
