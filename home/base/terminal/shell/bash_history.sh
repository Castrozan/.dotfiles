#!/usr/bin/env bash

# Remove duplicates from history
export HISTCONTROL=ignoreboth:erasedups
shopt -s histappend

# Increase the size of the history file
export HISTSIZE=10000
export HISTFILESIZE=20000

# Function to trim trailing spaces and replace the last command
trim_and_save_history() {
	local history_entry entry_number normalized_command
	local -a command_words
	history_entry=$(history 1)
	[[ "$history_entry" =~ ^[[:space:]]*([0-9]+)[[:space:]]+(.*)$ ]] || return
	entry_number="${BASH_REMATCH[1]}"
	read -r -a command_words <<<"${BASH_REMATCH[2]}"
	normalized_command="${command_words[*]}"
	history -d "$entry_number"
	history -s "$normalized_command"
}

# Set PROMPT_COMMAND to the custom function
_last_trimmed_histcmd=0
_history_prompt_command() {
	history -a
	if [[ "$HISTCMD" != "$_last_trimmed_histcmd" ]]; then
		_last_trimmed_histcmd="$HISTCMD"
		trim_and_save_history
	fi
}
PROMPT_COMMAND='_history_prompt_command'
