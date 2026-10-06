#!/usr/bin/env bash

export HISTCONTROL=ignorespace
export HISTTIMEFORMAT='%F %T '
shopt -s histappend

# Increase the size of the history file
export HISTSIZE=10000
export HISTFILESIZE=20000

# Function to trim trailing spaces and replace the last command
trim_and_save_history() {
	local history_entry entry_number normalized_command
	history_entry=$(HISTTIMEFORMAT='' builtin history 1)
	[[ "$history_entry" =~ ^[[:space:]]*([0-9]+)[[:space:]]+(.*)$ ]] || return
	entry_number="${BASH_REMATCH[1]}"
	if [[ "$entry_number" == "$_last_trimmed_histcmd" ]]; then
		return
	fi
	normalized_command="${BASH_REMATCH[2]}"
	normalized_command="${normalized_command%"${normalized_command##*[![:space:]]}"}"
	history -d "$entry_number"
	history -s "$normalized_command"
	_last_trimmed_histcmd="$entry_number"
}

record_recalled_command() {
	local recalled_command="${1-}"
	if [[ -o history ]]; then
		local history_entry
		history_entry=$(HISTTIMEFORMAT='' builtin history 1)
		[[ "$history_entry" =~ ^[[:space:]]*([0-9]+)[[:space:]]+ ]] || return 0
		if [[ "${BASH_REMATCH[1]}" != "$_last_trimmed_histcmd" ]]; then
			builtin history -s "$recalled_command"
		fi
	fi
}

# Set PROMPT_COMMAND to the custom function
_last_trimmed_histcmd=0
_history_prompt_command() {
	trim_and_save_history
	builtin history -a
}
PROMPT_COMMAND='_history_prompt_command'
