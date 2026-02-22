---
name: tmux
description: Tmux session and process control. Use when restarting dev servers, checking process output, stopping/starting background processes, or managing services in tmux panes.
---

<socket>
Hyprland sets TMUX_TMPDIR=$XDG_RUNTIME_DIR, placing the socket at /run/user/$UID/tmux-$UID/default. Bare tmux commands use /tmp and will fail silently with "no server running" even when sessions exist.

Detect socket once and bind a short alias for the entire script:

```sh
TMUX_SOCKET=$(find /run/user/$(id -u)/tmux-$(id -u) /tmp/tmux-$(id -u) -name default -type s 2>/dev/null | head -1)
t() { tmux -S "$TMUX_SOCKET" "$@"; }
```

Every command in the script then uses `t` instead of `tmux`. Never split socket detection and usage across separate bash invocations — the variable won't survive.
</socket>

<session_creation>
After `new-session -d`, the session exists but is not yet fully ready. Rename-window and send-keys on it immediately will fail with "can't find session". Always verify before operating:

```sh
t new-session -d -s "session-name" -n "first-window-name"
t list-sessions | grep -q "session-name" || { echo "session creation failed" >&2; exit 1; }
t new-window -t "session-name" -n "second-window-name"
t new-window -t "session-name" -n "third-window-name"
```

Use `-n` on `new-session` to name the first window at creation — it avoids a separate rename-window call that can race.
</session_creation>

<discovery>
List all windows: `t list-windows -a`
Output format: `session:window: window_name (n panes) [geometry] [flags]`

List panes in window: `t list-panes -t "session:window" -F "#{pane_index}: #{pane_current_command} - #{pane_current_path}"`
</discovery>

<targeting>
Format: `session:window.pane`. Window can be name or index. Session name must match exactly. Pane index depends on `pane-base-index` tmux option — always check with `t list-panes` before targeting. Do not assume index starts at 0.
</targeting>

<commands>
Send command: `t send-keys -t "session:window.pane" "command" Enter`
Stop process: `t send-keys -t "session:window.pane" C-c` (no Enter after C-c)
Capture output: `t capture-pane -t "session:window.pane" -p`
With scrollback: `t capture-pane -t target -p -S -50 | tail -30`
</commands>

<dev_server_restart>
1. Find pane: `t list-windows -a`
2. Identify process: `t list-panes -t "session:window" -F "#{pane_index}: #{pane_current_command}"`
3. Stop: `t send-keys -t target C-c`
4. Verify stopped via capture
5. Start: `t send-keys -t target "yarn start" Enter`
6. Verify started via capture after brief delay
</dev_server_restart>

<error_recovery>
"can't find session" after new-session: race condition — verify with list-sessions before operating on it. "no server running": socket path wrong — use the /run/user/ path. Command not executing: verify target exists first. Process not stopping: send C-c multiple times. Output garbled: use -J flag.
</error_recovery>

<practices>
Always verify target pane before sending. Capture output before and after operations. Check pane_current_command to confirm state. Never assume pane state. Never split socket detection and usage across bash invocations.
</practices>
