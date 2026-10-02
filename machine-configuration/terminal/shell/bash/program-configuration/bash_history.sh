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
	normalized_command="${BASH_REMATCH[2]}"
	normalized_command="${normalized_command%"${normalized_command##*[![:space:]]}"}"
	history -d "$entry_number"
	history -s "$normalized_command"
}

record_recalled_command() {
	if [[ -o history && "$HISTCMD" != "$_last_trimmed_histcmd" ]]; then
		builtin history -s "$1"
	fi
}

# Set PROMPT_COMMAND to the custom function
_last_trimmed_histcmd=0
_history_prompt_command() {
	if [[ "$HISTCMD" != "$_last_trimmed_histcmd" ]]; then
		trim_and_save_history
		_last_trimmed_histcmd="$HISTCMD"
	fi
	builtin history -a
}
PROMPT_COMMAND='_history_prompt_command'
