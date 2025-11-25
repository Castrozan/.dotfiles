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

        # Send first command to the initial pane (full pane, left side)
        # Note: tmux panes are 1-indexed, not 0-indexed
        tmux send-keys -t screensaver.1 "$first_cmd" C-m

        # For remaining commands, create right side panes
        # Layout: Left (large) = first command, Right side = remaining commands
        # If 3 commands: top-right = third, bottom-right = second
        if [ ${#available_commands[@]} -gt 1 ]; then
            # Split horizontally to create right side (pane 2)
            tmux split-window -h -t screensaver.1
            
            # If there are 3 commands: create vertical split on right side
            if [ ${#available_commands[@]} -gt 2 ]; then
                # Send third command (cmatrix) to top-right (pane 2)
                tmux send-keys -t screensaver.2 "${available_commands[2]}" C-m
                # Split pane 2 vertically to create bottom-right pane (pane 3)
                tmux split-window -v -t screensaver.2
                # Send second command (pipes.sh) to the bottom-right pane (pane 3)
                tmux send-keys -t screensaver.3 "${available_commands[1]}" C-m
            else
                # Only 2 commands: second goes to right pane
                tmux send-keys -t screensaver.2 "${available_commands[1]}" C-m
            fi
        fi

        # Select the first pane (left side, bonsai)
        tmux select-pane -t screensaver.1
    fi
}

