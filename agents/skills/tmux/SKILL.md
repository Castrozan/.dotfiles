---
name: tmux
description: Tmux session and process control. Use when restarting dev servers, checking process output, stopping/starting background processes, or managing services in tmux panes.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<socket>
The tmux socket path depends on TMUX_TMPDIR. Hyprland sets TMUX_TMPDIR=$XDG_RUNTIME_DIR, placing the socket at /run/user/$UID/tmux-$UID/default instead of the default /tmp/tmux-$UID/default. If TMUX_TMPDIR is set in the agent environment (via env.vars in openclaw.json), bare tmux commands work. If not, detect and use the correct socket:

Detect socket: TMUX_SOCKET=$(find /run/user/$(id -u)/tmux-$(id -u) /tmp/tmux-$(id -u) -name default -type s 2>/dev/null | head -1)
Use explicit socket: tmux -S "$TMUX_SOCKET" list-sessions

If bare `tmux list-sessions` returns "no server running" but sessions exist, the socket path is wrong. Try the /run/user/ path.
</socket>

<discovery>
List all windows: tmux list-windows -a
Output format: session:window: window_name (n panes) [geometry] [flags]

List panes in window: tmux list-panes -t "session:window" -F "#{pane_index}: #{pane_current_command} - #{pane_current_path}"
</discovery>

<targeting>
Format: session:window.pane (pane is 0-indexed). Window can be name or index. If single pane, .0 optional. Session name must match exactly.
</targeting>

<commands>
Send command: tmux send-keys -t "session:window.pane" "command" Enter
Stop process: tmux send-keys -t "session:window.pane" C-c (no Enter after C-c)
Capture output: tmux capture-pane -t "session:window.pane" -p
With scrollback: tmux capture-pane -t target -p -S -50 | tail -30
</commands>

<dev_server_restart>
1. Find pane: tmux list-windows -a
2. Identify process: tmux list-panes -t "session:window" -F "#{pane_index}: #{pane_current_command}"
3. Stop: tmux send-keys -t target C-c
4. Verify stopped via capture
5. Start: tmux send-keys -t target "yarn start" Enter
6. Verify started via capture after delay
</dev_server_restart>

<error_recovery>
Command not executing: verify target exists with list-windows/list-panes. Process not stopping: try multiple C-c sends. Output garbled: use -J flag for join lines. Socket wrong: if "no server running" appears, check TMUX_TMPDIR or use -S with the /run/user/ socket path.
</error_recovery>

<practices>
Always verify target pane before sending. Capture output before and after operations. Use delay between stop and start. Check pane current_command to confirm state. Never assume pane state.
</practices>
