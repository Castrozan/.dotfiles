#!/usr/bin/env bash

# Check if a command is available by trying to run it
# Returns 0 if command exists and can be run, 1 otherwise
_check_command_available() {
    local cmd="$1"

    # Extract the first word (base command) from the command string
    local base_cmd
    base_cmd=$(echo "$cmd" | awk '{print $1}')

    # Check if the base command exists
    if command -v "$base_cmd" &>/dev/null; then
        return 0
    fi

    return 1
}

# Start the screensaver tmux session
_start_screensaver_tmux_session() {
    # Check if the screensaver session already exists
    if tmux has-session -t screensaver 2>/dev/null; then
        return 0
    fi

    # Filter available commands
    local available_commands=()
    for cmd in "${SCREENSAVER_COMMANDS[@]}"; do
        if _check_command_available "$cmd"; then
            available_commands+=("$cmd")
        fi
    done

    # Create screensaver session (even if empty)
    tmux new-session -d -s screensaver -n screensaver

    # If we have available commands, set them up
    if [ ${#available_commands[@]} -gt 0 ]; then
        local first_cmd="${available_commands[0]}"

        # Send first command to the initial pane (full pane)
        tmux send-keys -t screensaver.0 "$first_cmd" C-m

        # Split horizontally for remaining commands
        # Each split creates a new pane; use '-' to target the last created pane
        for i in $(seq 1 $((${#available_commands[@]} - 1))); do
            # Split the first pane (pane 0) horizontally
            tmux split-window -h -t screensaver.0
            # Send command to the newly created pane (last pane)
            tmux send-keys -t screensaver:- "${available_commands[$i]}" C-m
        done

        # Select the first pane
        tmux select-pane -t screensaver.0
    fi
}

