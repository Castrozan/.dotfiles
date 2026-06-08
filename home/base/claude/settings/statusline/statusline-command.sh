#!/usr/bin/env bash
set -Eeuo pipefail
export LC_NUMERIC=C

# shellcheck disable=SC2034
{
	readonly COLOR_CYAN='\033[36m'
	readonly COLOR_YELLOW='\033[33m'
	readonly COLOR_GREEN='\033[32m'
	readonly COLOR_MAGENTA='\033[35m'
	readonly COLOR_RED='\033[31m'
	readonly COLOR_DIM='\033[2m'
	readonly COLOR_RESET='\033[0m'
	readonly SEGMENT_SEPARATOR="${COLOR_DIM}│${COLOR_RESET}"
	readonly GIT_CACHE_TTL_SECONDS=5
	readonly GIT_CACHE_MIN_TRACKED_FILES_FOR_CACHING=500
}

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/statusline-command-git-segment.sh"
# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/statusline-command-json-segments.sh"

_read_stdin_json_input() {
	cat
}

_append_segment_to_output() {
	local current_output="$1"
	local new_segment="$2"

	if [ -z "$new_segment" ]; then
		echo "$current_output"
		return 0
	fi

	if [ -z "$current_output" ]; then
		echo "$new_segment"
	else
		echo "${current_output} ${SEGMENT_SEPARATOR} ${new_segment}"
	fi
}

_render_statusline_from_json_input() {
	local json_input="$1"
	local current_working_directory
	current_working_directory=$(echo "$json_input" | jq -r '.cwd')

	local git_segment model_segment context_window_segment rate_limit_segment session_id_segment

	git_segment=$(_build_git_segment_from_repo_directory "$current_working_directory")
	model_segment=$(_build_model_segment_from_json_input "$json_input")
	context_window_segment=$(_build_context_window_segment_from_json_input "$json_input")
	rate_limit_segment=$(_build_rate_limit_five_hour_segment_from_json_input "$json_input")
	session_id_segment=$(_build_session_id_segment_from_json_input "$json_input")

	local statusline=""
	statusline=$(_append_segment_to_output "$statusline" "$git_segment")
	statusline=$(_append_segment_to_output "$statusline" "$model_segment")
	statusline=$(_append_segment_to_output "$statusline" "$context_window_segment")
	statusline=$(_append_segment_to_output "$statusline" "$rate_limit_segment")
	statusline=$(_append_segment_to_output "$statusline" "$session_id_segment")

	printf "%b" "$statusline"
}

main() {
	local json_input
	json_input=$(_read_stdin_json_input)
	_render_statusline_from_json_input "$json_input"
}

main
