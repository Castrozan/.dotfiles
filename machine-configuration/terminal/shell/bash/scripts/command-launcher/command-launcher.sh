#!/usr/bin/env bash

cx() {
	if [[ $# -eq 0 ]]; then
		printf 'Usage: cx <keywords...>\n' >&2
		return 2
	fi
	if [[ ${command_launcher_active:-0} -eq 1 ]]; then
		printf 'cx: recursive command recall refused\n' >&2
		return 2
	fi
	if [[ -z ${HISTFILE:-} ]]; then
		printf 'cx: command history is disabled\n' >&2
		return 1
	fi
	if ! command -v command-history-ranker >/dev/null 2>&1; then
		printf 'cx: command history ranker is unavailable\n' >&2
		return 1
	fi
	if [[ -o history ]]; then
		builtin history -a || return
	fi
	local command_launcher_active=1 selected_command ranker_process
	local -a ranked_commands
	mapfile -d '' -t ranked_commands < <(HISTFILE="$HISTFILE" HSTR_CONFIG=keywords-matching command command-history-ranker --non-interactive "$@")
	ranker_process=$!
	wait "$ranker_process" || return
	for selected_command in "${ranked_commands[@]}"; do
		if [[ -z $selected_command || $selected_command == cx || $selected_command == cx[[:space:]]* ]]; then
			continue
		fi
		printf '%s\n' "$selected_command" >&2
		record_recalled_command "$selected_command"
		builtin eval -- "$selected_command"
		return $?
	done
	printf 'cx: no matching command\n' >&2
	return 1
}
