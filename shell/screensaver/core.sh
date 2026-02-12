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

# Wait for a tmux pane's shell to be ready (showing a prompt)
_wait_for_pane_ready() {
    local pane="$1"
    local max_attempts=30  # 3 seconds max
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        # Check if the pane has a shell prompt (cursor at end of line with $)
        local content
        content=$(tmux capture-pane -t "$pane" -p 2>/dev/null | grep -c '\$')
        if [ "$content" -gt 0 ]; then
            return 0
        fi
        sleep 0.1
        attempt=$((attempt + 1))
    done
    return 1
}

_start_screensaver_tmux_session() {
    # Filter available commands
    local available_commands=()
    for cmd in "${SCREENSAVER_COMMANDS[@]}"; do
        if _check_command_available "$cmd"; then
            available_commands+=("$cmd")
        fi
    done

    # Create screensaver session (fails atomically if session already exists)
    if ! tmux new-session -d -s screensaver -n screensaver 2>/dev/null; then
        return 0
    fi

    if [ ${#available_commands[@]} -gt 0 ]; then
        local first_cmd="${available_commands[0]}"

        if [ ${#available_commands[@]} -gt 1 ]; then
            # Split horizontally: right pane (pane 2) gets 20% width
            tmux split-window -h -p 20 -t screensaver.1

            if [ ${#available_commands[@]} -gt 2 ]; then
                # Split right pane vertically: bottom-right (pane 3) gets 50% height
                tmux split-window -v -p 50 -t screensaver.2
            fi
        fi

        # Wait for all panes to be ready, then send commands
        _wait_for_pane_ready "screensaver.1"
        tmux send-keys -t screensaver.1 "$first_cmd" C-m

        if [ ${#available_commands[@]} -gt 2 ]; then
            # Pane 2 = top-right, pane 3 = bottom-right
            _wait_for_pane_ready "screensaver.2"
            tmux send-keys -t screensaver.2 "${available_commands[1]}" C-m

            _wait_for_pane_ready "screensaver.3"
            tmux send-keys -t screensaver.3 "${available_commands[2]}" C-m
        elif [ ${#available_commands[@]} -gt 1 ]; then
            _wait_for_pane_ready "screensaver.2"
            tmux send-keys -t screensaver.2 "${available_commands[1]}" C-m
        fi

        # Focus back to the first pane
        tmux select-pane -t screensaver.1
    fi
}
