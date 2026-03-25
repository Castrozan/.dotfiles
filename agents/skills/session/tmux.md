<socket_trap>
Hyprland sets TMUX_TMPDIR=$XDG_RUNTIME_DIR, placing the socket at /run/user/$UID/tmux-$UID/default. Bare tmux commands use /tmp and will fail silently with "no server running" even when sessions exist.

Detect socket once and bind a short alias for the entire script:

```sh
TMUX_SOCKET=$(find /run/user/$(id -u)/tmux-$(id -u) /tmp/tmux-$(id -u) -name default -type s 2>/dev/null | head -1)
t() { tmux -S "$TMUX_SOCKET" "$@"; }
```

Never split socket detection and usage across separate bash invocations — the variable won't survive.
</socket_trap>

<session_creation_race>
After `new-session -d`, the session exists but is not yet fully ready. Rename-window and send-keys on it immediately will fail with "can't find session". Always verify with list-sessions before operating on new sessions. Use `-n` on `new-session` to name the first window at creation — it avoids a separate rename-window call that can race.
</session_creation_race>

<targeting_pitfall>
Pane index depends on `pane-base-index` tmux option — always check with list-panes before targeting. Do not assume index starts at 0. No Enter after C-c when stopping processes.
</targeting_pitfall>

<error_recovery>
"can't find session" after new-session: race condition — verify with list-sessions before operating. "no server running": socket path wrong — use the /run/user/ path. Process not stopping: send C-c multiple times. Output garbled: use -J flag.
</error_recovery>

<practices>
Always verify target pane before sending. Capture output before and after operations. Check pane_current_command to confirm state. Never assume pane state.
</practices>
