#!/usr/bin/env bash

_check_command_available() {
    local cmd="$1"

    # Extract the first word (base command) from the command string
    local base_cmd
    base_cmd=$(echo "$cmd" | awk '{print $1}')

    if command -v "$base_cmd" &>/dev/null; then
        return 0
    fi

    return 1
}

_start_screensaver_tmux_session() {
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

    # Create screensaver session
    tmux new-session -d -s screensaver -n screensaver

    if [ ${#available_commands[@]} -gt 0 ]; then
        local first_cmd="${available_commands[0]}"

        # Send first command to the initial pane (full pane, left side)
        # Note: tmux panes are 1-indexed, not 0-indexed
        tmux send-keys -t screensaver.1 "$first_cmd" C-m

        local bottom_height="${SCREENSAVER_BOTTOM_HEIGHT:-15}"

        if [ ${#available_commands[@]} -gt 1 ]; then
            # Split horizontally to create right side (pane 2)
            tmux split-window -h -t screensaver.1

            # If there are 3 commands: create vertical split on right side
            if [ ${#available_commands[@]} -gt 2 ]; then
                # Send third command to pane 2
                tmux send-keys -t screensaver.2 "${available_commands[2]}" C-m

                # Split pane 2 vertically to create bottom-right pane (pane 3)
                tmux split-window -v -p "$bottom_height" -t screensaver.2
                # Send second command to pane 3
                tmux send-keys -t screensaver.3 "${available_commands[1]}" C-m
            else
                # Send third command to pane 2
                tmux send-keys -t screensaver.2 "${available_commands[1]}" C-m
            fi
        fi

        # Focus back to the first pane
        tmux select-pane -t screensaver.1
    fi
}

