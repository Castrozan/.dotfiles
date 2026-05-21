# shellcheck shell=bash

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

	printf "${COLOR_DIM}ctx ${context_color}%s%%${COLOR_RESET}" "$rounded_used_percentage"
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

	printf "${COLOR_DIM}lim ${limit_color}%s%%${COLOR_DIM}%s${COLOR_RESET}" "$rounded_percentage" "$reset_remaining"
}

_build_session_id_segment_from_json_input() {
	local json_input="$1"
	local session_id
	session_id=$(echo "$json_input" | jq -r '.session_id // empty')
	[ -z "$session_id" ] && return 0
	printf "${COLOR_DIM}%s${COLOR_RESET}" "$session_id"
}
