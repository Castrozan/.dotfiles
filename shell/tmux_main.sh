#!/usr/bin/env bash

# Function to start a main tmux session
_start_main_tmux_session() {
    # Check if the main session exists
    if ! tmux has-session -t main 2>/dev/null; then
        tmux new-session -d -s main -n main
    fi
}

