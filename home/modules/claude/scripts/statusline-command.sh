#!/usr/bin/env bash
set -Eeuo pipefail
export LC_NUMERIC=C

readonly COLOR_CYAN='\033[36m'
readonly COLOR_YELLOW='\033[33m'
readonly COLOR_GREEN='\033[32m'
readonly COLOR_MAGENTA='\033[35m'
readonly COLOR_RED='\033[31m'
readonly COLOR_DIM='\033[2m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_RESET='\033[0m'

readonly SEGMENT_SEPARATOR="${COLOR_DIM}│${COLOR_RESET}"
readonly GIT_CACHE_TTL_SECONDS=5
readonly GIT_CACHE_MIN_TRACKED_FILES_FOR_CACHING=500

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

_git_cache_file_for_directory() {
	local directory="$1"
	local hashed_directory
	hashed_directory=$(echo "$directory" | md5sum | cut -d' ' -f1)
	echo "/tmp/claude-statusline-git-${hashed_directory}"
}

_repo_has_enough_files_to_benefit_from_caching() {
	local directory="$1"
	local tracked_file_count
	tracked_file_count=$(git -C "$directory" --no-optional-locks ls-files 2>/dev/null | wc -l) || return 1
	[ "$tracked_file_count" -ge "$GIT_CACHE_MIN_TRACKED_FILES_FOR_CACHING" ]
}

_git_cache_is_still_valid() {
	local cache_file="$1"
	[ -f "$cache_file" ] || return 1
	local cache_age_seconds
	cache_age_seconds=$(($(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || echo 0)))
	[ "$cache_age_seconds" -lt "$GIT_CACHE_TTL_SECONDS" ]
}

_build_git_segment_from_repo_directory() {
	local repository_directory="$1"

	cd "$repository_directory" || return 0

	local cache_file
	cache_file=$(_git_cache_file_for_directory "$repository_directory")

	if _repo_has_enough_files_to_benefit_from_caching "$repository_directory" && _git_cache_is_still_valid "$cache_file"; then
		cat "$cache_file"
		return 0
	fi

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

	local git_segment
	git_segment=$(printf "${COLOR_GREEN}%s%s%s${COLOR_RESET}" "$branch_name" "$dirty_marker" "$ahead_behind_counts")

	if _repo_has_enough_files_to_benefit_from_caching "$repository_directory"; then
		echo "$git_segment" >"$cache_file"
	fi

	printf "%s" "$git_segment"
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
	local total_cost_usd
	total_cost_usd=$(echo "$json_input" | jq -r '.cost.total_cost_usd // empty')
	[ -z "$total_cost_usd" ] && return 0

	local formatted_cost
	formatted_cost=$(printf "%.2f" "$total_cost_usd")

	local cost_color
	if awk "BEGIN {exit !($total_cost_usd >= 1.00)}"; then
		cost_color="$COLOR_RED"
	elif awk "BEGIN {exit !($total_cost_usd >= 0.25)}"; then
		cost_color="$COLOR_YELLOW"
	else
		cost_color="$COLOR_GREEN"
	fi

	printf "${cost_color}\$%s${COLOR_RESET}" "$formatted_cost"
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

_build_agent_name_segment_from_json_input() {
	local json_input="$1"
	local agent_name
	agent_name=$(echo "$json_input" | jq -r '.agent.name // empty')
	[ -z "$agent_name" ] && return 0
	printf "${COLOR_BOLD}${COLOR_CYAN}⚡%s${COLOR_RESET}" "$agent_name"
}

_build_worktree_segment_from_json_input() {
	local json_input="$1"
	local worktree_name
	worktree_name=$(echo "$json_input" | jq -r '.worktree.name // empty')
	[ -z "$worktree_name" ] && return 0
	local worktree_branch
	worktree_branch=$(echo "$json_input" | jq -r '.worktree.branch // empty')
	if [ -n "$worktree_branch" ]; then
		printf "${COLOR_YELLOW}🌿%s${COLOR_DIM}→%s${COLOR_RESET}" "$worktree_name" "$worktree_branch"
	else
		printf "${COLOR_YELLOW}🌿%s${COLOR_RESET}" "$worktree_name"
	fi
}

_build_rate_limit_five_hour_segment_from_json_input() {
	local json_input="$1"
	local five_hour_used_percentage
	five_hour_used_percentage=$(echo "$json_input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
	[ -z "$five_hour_used_percentage" ] && return 0

	local rounded_percentage
	rounded_percentage=$(printf "%.0f" "$five_hour_used_percentage")

	local resets_at_epoch
	resets_at_epoch=$(echo "$json_input" | jq -r '.rate_limits.five_hour.resets_at // empty')

	local reset_remaining=""
	if [ -n "$resets_at_epoch" ]; then
		local now_epoch
		now_epoch=$(date +%s)
		local seconds_remaining=$((resets_at_epoch - now_epoch))
		if [ "$seconds_remaining" -gt 0 ]; then
			local hours_remaining=$((seconds_remaining / 3600))
			local minutes_remaining=$(((seconds_remaining % 3600) / 60))
			if [ "$hours_remaining" -gt 0 ]; then
				reset_remaining=" ${hours_remaining}h${minutes_remaining}m"
			else
				reset_remaining=" ${minutes_remaining}m"
			fi
		fi
	fi

	local limit_color
	if [ "$rounded_percentage" -ge 80 ]; then
		limit_color="$COLOR_RED"
	elif [ "$rounded_percentage" -ge 50 ]; then
		limit_color="$COLOR_YELLOW"
	else
		limit_color="$COLOR_GREEN"
	fi

	printf "${COLOR_DIM}limit ${limit_color}%s%%${COLOR_DIM} resets in%s${COLOR_RESET}" "$rounded_percentage" "$reset_remaining"
}

_format_duration_from_milliseconds() {
	local total_milliseconds="$1"
	local total_seconds=$((total_milliseconds / 1000))
	local hours=$((total_seconds / 3600))
	local minutes=$(((total_seconds % 3600) / 60))
	local seconds=$((total_seconds % 60))

	if [ "$hours" -gt 0 ]; then
		printf "%dh%02dm" "$hours" "$minutes"
	elif [ "$minutes" -gt 0 ]; then
		printf "%dm%02ds" "$minutes" "$seconds"
	else
		printf "%ds" "$seconds"
	fi
}

_build_session_duration_segment_from_json_input() {
	local json_input="$1"
	local total_duration_ms
	total_duration_ms=$(echo "$json_input" | jq -r '.cost.total_duration_ms // empty')
	[ -z "$total_duration_ms" ] && return 0
	[ "$total_duration_ms" -eq 0 ] 2>/dev/null && return 0

	local formatted_duration
	formatted_duration=$(_format_duration_from_milliseconds "$total_duration_ms")

	printf "${COLOR_DIM}session %s${COLOR_RESET}" "$formatted_duration"
}

_build_lines_changed_segment_from_json_input() {
	local json_input="$1"
	local lines_added lines_removed
	lines_added=$(echo "$json_input" | jq -r '.cost.total_lines_added // 0')
	lines_removed=$(echo "$json_input" | jq -r '.cost.total_lines_removed // 0')

	if [ "$lines_added" -eq 0 ] && [ "$lines_removed" -eq 0 ]; then
		return 0
	fi

	local output=""
	[ "$lines_added" -gt 0 ] && output="${COLOR_GREEN}+${lines_added}${COLOR_RESET}"
	if [ "$lines_removed" -gt 0 ]; then
		[ -n "$output" ] && output="${output}${COLOR_DIM}/${COLOR_RESET}"
		output="${output}${COLOR_RED}-${lines_removed}${COLOR_RESET}"
	fi

	printf "%b" "$output"
}

_build_transcript_path_segment_from_json_input() {
	local json_input="$1"
	local transcript_path
	transcript_path=$(echo "$json_input" | jq -r '.transcript_path // empty')
	[ -z "$transcript_path" ] && return 0

	local transcript_filename
	transcript_filename=$(basename "$transcript_path")
	printf "${COLOR_DIM}log %s${COLOR_RESET}" "$transcript_filename"
}

_render_statusline_from_json_input() {
	local json_input="$1"
	local current_working_directory
	current_working_directory=$(echo "$json_input" | jq -r '.cwd')

	local vim_mode_segment session_id_segment agent_name_segment worktree_segment
	local session_name_segment git_segment model_segment
	local session_cost_segment rate_limit_segment session_duration_segment
	local lines_changed_segment context_window_segment transcript_path_segment

	vim_mode_segment=$(_build_vim_mode_segment_from_json_input "$json_input")
	session_id_segment=$(_build_session_id_segment_from_json_input "$json_input")
	agent_name_segment=$(_build_agent_name_segment_from_json_input "$json_input")
	worktree_segment=$(_build_worktree_segment_from_json_input "$json_input")
	session_name_segment=$(_build_session_name_segment_from_json_input "$json_input")
	git_segment=$(_build_git_segment_from_repo_directory "$current_working_directory")
	model_segment=$(_build_model_segment_from_json_input "$json_input")

	session_cost_segment=$(_build_session_cost_segment_from_json_input "$json_input")
	rate_limit_segment=$(_build_rate_limit_five_hour_segment_from_json_input "$json_input")
	session_duration_segment=$(_build_session_duration_segment_from_json_input "$json_input")
	lines_changed_segment=$(_build_lines_changed_segment_from_json_input "$json_input")
	context_window_segment=$(_build_context_window_segment_from_json_input "$json_input")
	transcript_path_segment=$(_build_transcript_path_segment_from_json_input "$json_input")

	local line_one=""
	line_one=$(_append_segment_to_output "$line_one" "$vim_mode_segment")
	line_one=$(_append_segment_to_output "$line_one" "$session_id_segment")
	line_one=$(_append_segment_to_output "$line_one" "$agent_name_segment")
	line_one=$(_append_segment_to_output "$line_one" "$worktree_segment")
	line_one=$(_append_segment_to_output "$line_one" "$session_name_segment")
	line_one=$(_append_segment_to_output "$line_one" "$git_segment")
	line_one=$(_append_segment_to_output "$line_one" "$model_segment")

	local line_two=""
	line_two=$(_append_segment_to_output "$line_two" "$session_cost_segment")
	line_two=$(_append_segment_to_output "$line_two" "$rate_limit_segment")
	line_two=$(_append_segment_to_output "$line_two" "$session_duration_segment")
	line_two=$(_append_segment_to_output "$line_two" "$lines_changed_segment")
	line_two=$(_append_segment_to_output "$line_two" "$context_window_segment")
	line_two=$(_append_segment_to_output "$line_two" "$transcript_path_segment")

	printf "%b\n" "$line_one"
	printf "%b" "$line_two"
}

main() {
	local json_input
	json_input=$(_read_stdin_json_input)
	_render_statusline_from_json_input "$json_input"
}

main
