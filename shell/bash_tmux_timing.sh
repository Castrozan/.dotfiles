#!/usr/bin/env bash

# Per-pane command timing for tmux
# Sets pane-local tmux option to track command execution time
# Timer is displayed in tmux status bar via settings.conf

__tmux_cmd_start() {
  [[ -n "$TMUX" ]] || return
  tmux set-option -p pane_cmd_start "$(date +%s)" >/dev/null 2>&1
}

__tmux_cmd_end() {
  [[ -n "$TMUX" ]] || return
  tmux set-option -p -u pane_cmd_start >/dev/null 2>&1
}

# Run before every command
trap '__tmux_cmd_start' DEBUG

# Run after command finishes (before prompt)
PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND; }__tmux_cmd_end"

