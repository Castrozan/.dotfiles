#!/usr/bin/env bash
set -Eeuo pipefail

readonly COLOR_CYAN='\033[36m'
readonly COLOR_YELLOW='\033[33m'
readonly COLOR_GREEN='\033[32m'
readonly COLOR_MAGENTA='\033[35m'
readonly COLOR_RED='\033[31m'
readonly COLOR_DIM='\033[2m'
readonly COLOR_RESET='\033[0m'

readonly SEGMENT_SEPARATOR="${COLOR_DIM}│${COLOR_RESET}"

_read_stdin_json_input() {
	cat
}

_build_git_segment_from_repo_directory() {
	local repository_directory="$1"

	cd "$repository_directory" || return 0

	local branch_name
	branch_name=$(git --no-optional-locks branch --show-current 2>/dev/null) || return 0
	[ -z "$branch_name" ] && return 0

	local dirty_marker=""
	if ! git --no-optional-locks diff --quiet 2>/dev/null || ! git --no-optional-locks diff --cached --quiet 2>/dev/null; then
		dirty_marker="*"
	fi

	local upstream_tracking_ref
	upstream_tracking_ref=$(git --no-optional-locks rev-parse --abbrev-ref "@{upstream}" 2>/dev/null) || upstream_tracking_ref=""

	local ahead_behind_counts=""
	if [ -n "$upstream_tracking_ref" ]; then
		local ahead_count behind_count
		ahead_count=$(git --no-optional-locks rev-list --count "@{upstream}..HEAD" 2>/dev/null) || ahead_count=0
		behind_count=$(git --no-optional-locks rev-list --count "HEAD..@{upstream}" 2>/dev/null) || behind_count=0

		[ "$ahead_count" -gt 0 ] && ahead_behind_counts="${ahead_behind_counts}↑${ahead_count}"
		[ "$behind_count" -gt 0 ] && ahead_behind_counts="${ahead_behind_counts}↓${behind_count}"
		[ -n "$ahead_behind_counts" ] && ahead_behind_counts=" ${ahead_behind_counts}"
	fi

	printf "${COLOR_GREEN}%s%s%s${COLOR_RESET}" "$branch_name" "$dirty_marker" "$ahead_behind_counts"
}

_build_model_segment_from_json_input() {
	local json_input="$1"
	local model_display_name
	model_display_name=$(echo "$json_input" | jq -r '.model.display_name // empty')
	[ -z "$model_display_name" ] && return 0
	printf "${COLOR_CYAN}%s${COLOR_RESET}" "$model_display_name"
}

_build_context_window_segment_from_json_input() {
	local json_input="$1"

	local used_percentage
	used_percentage=$(echo "$json_input" | jq -r '.context_window.used_percentage // empty')
	[ -z "$used_percentage" ] && return 0

	local rounded_used_percentage
	rounded_used_percentage=$(printf "%.0f" "$used_percentage")

	local context_color
	if [ "$rounded_used_percentage" -ge 80 ]; then
		context_color="$COLOR_RED"
	elif [ "$rounded_used_percentage" -ge 50 ]; then
		context_color="$COLOR_YELLOW"
	else
		context_color="$COLOR_MAGENTA"
	fi

	local progress_bar_total_width=10
	local filled_width=$((rounded_used_percentage * progress_bar_total_width / 100))
	local empty_width=$((progress_bar_total_width - filled_width))

	local filled_characters=""
	local empty_characters=""
	for ((i = 0; i < filled_width; i++)); do filled_characters+="█"; done
	for ((i = 0; i < empty_width; i++)); do empty_characters+="░"; done

	printf "${context_color}%s${COLOR_DIM}%s${COLOR_RESET} ${context_color}%s%%${COLOR_RESET}" "$filled_characters" "$empty_characters" "$rounded_used_percentage"
}

_build_session_cost_segment_from_json_input() {
	local json_input="$1"

	local total_input_tokens total_output_tokens
	total_input_tokens=$(echo "$json_input" | jq -r '.context_window.total_input_tokens // 0')
	total_output_tokens=$(echo "$json_input" | jq -r '.context_window.total_output_tokens // 0')

	if [ "$total_input_tokens" -eq 0 ] && [ "$total_output_tokens" -eq 0 ]; then
		return 0
	fi

	local estimated_cost_in_dollars
	estimated_cost_in_dollars=$(awk "BEGIN {printf \"%.2f\", ($total_input_tokens * 3.00 + $total_output_tokens * 15.00) / 1000000}")

	local cost_color
	if awk "BEGIN {exit !($estimated_cost_in_dollars >= 1.00)}"; then
		cost_color="$COLOR_RED"
	elif awk "BEGIN {exit !($estimated_cost_in_dollars >= 0.25)}"; then
		cost_color="$COLOR_YELLOW"
	else
		cost_color="$COLOR_GREEN"
	fi

	printf "${cost_color}\$%s${COLOR_RESET}" "$estimated_cost_in_dollars"
}

_build_session_id_segment_from_json_input() {
	local json_input="$1"
	local session_id
	session_id=$(echo "$json_input" | jq -r '.session_id // empty')
	[ -z "$session_id" ] && return 0
	local short_session_id="${session_id:0:8}"
	printf "${COLOR_DIM}%s${COLOR_RESET}" "$short_session_id"
}

_build_session_name_segment_from_json_input() {
	local json_input="$1"
	local session_name
	session_name=$(echo "$json_input" | jq -r '.session_name // empty')
	[ -z "$session_name" ] && return 0
	printf "${COLOR_DIM}%s${COLOR_RESET}" "$session_name"
}

_build_vim_mode_segment_from_json_input() {
	local json_input="$1"
	local vim_mode
	vim_mode=$(echo "$json_input" | jq -r '.vim.mode // empty')
	[ -z "$vim_mode" ] && return 0

	local vim_color
	if [ "$vim_mode" = "INSERT" ]; then
		vim_color="$COLOR_GREEN"
	else
		vim_color="$COLOR_YELLOW"
	fi

	printf "${vim_color}%s${COLOR_RESET}" "$vim_mode"
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

	local git_segment model_segment context_window_segment session_name_segment vim_mode_segment session_cost_segment session_id_segment
	git_segment=$(_build_git_segment_from_repo_directory "$current_working_directory")
	model_segment=$(_build_model_segment_from_json_input "$json_input")
	context_window_segment=$(_build_context_window_segment_from_json_input "$json_input")
	session_name_segment=$(_build_session_name_segment_from_json_input "$json_input")
	vim_mode_segment=$(_build_vim_mode_segment_from_json_input "$json_input")
	session_cost_segment=$(_build_session_cost_segment_from_json_input "$json_input")
	session_id_segment=$(_build_session_id_segment_from_json_input "$json_input")

	local output=""
	output=$(_append_segment_to_output "$output" "$vim_mode_segment")
	output=$(_append_segment_to_output "$output" "$session_id_segment")
	output=$(_append_segment_to_output "$output" "$session_name_segment")
	output=$(_append_segment_to_output "$output" "$git_segment")
	output=$(_append_segment_to_output "$output" "$model_segment")
	output=$(_append_segment_to_output "$output" "$session_cost_segment")
	output=$(_append_segment_to_output "$output" "$context_window_segment")

	printf "%b" "$output"
}

main() {
	local json_input
	json_input=$(_read_stdin_json_input)
	_render_statusline_from_json_input "$json_input"
}

main
