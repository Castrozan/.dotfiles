#!/bin/bash

# Remove duplicates from history
export HISTCONTROL=ignoreboth:erasedups
shopt -s histappend

# Increase the size of the history file
export HISTSIZE=10000
export HISTFILESIZE=20000

# Function to trim trailing spaces and replace the last command
trim_and_save_history() {
    # Extract the current command (excluding history number)
    local current_command=$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//' | awk '{$1=$1};1')

    # Remove the last command in history
    history -d $(history | tail -n 1 | awk '{print $1}')

    # Add the trimmed command to history
    history -s "$current_command"
}

# Set PROMPT_COMMAND to the custom function
PROMPT_COMMAND='history -a; trim_and_save_history'