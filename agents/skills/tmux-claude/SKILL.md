---
name: tmux-claude
description: Spawn and drive a second Claude Code session in a tmux window you can watch or take over - send prompts, read output, resume by id. Use to hand off a background Claude.
---

<when_to_spawn>
Spawn a tmux session when the user needs to watch or take over the work, when it benefits from a persistent interactive session, or when it must outlive your own conversation. For read-only research, codebase exploration, or file search, use the builtin Agent tool instead - no tmux. For multi-agent work that edits code, run a Workflow (see the `deliver` skill) with worktree isolation, never Teams.
</when_to_spawn>

<spawning>
`spawn-claude` is on PATH everywhere; it creates the target tmux session if it does not yet exist (otherwise adds a window to it), starts claude, waits for the input prompt, then optionally sends an initial prompt. Run `spawn-claude --help` for targets and flags rather than memorizing them. Pass a multi-line initial prompt via `--file`, never inline, so it is not submitted line by line.
</spawning>

<socket_fails_silently>
tmux's socket is not always at the default path (Hyprland and macOS place it under a runtime dir), so bare `tmux` reports "no server running" even when sessions exist. Detect it once and reuse it; never split detection and use across separate bash invocations, the variable will not survive: `TMUX_SOCKET=$(find /run/user/$(id -u)/tmux-$(id -u) /tmp/tmux-$(id -u) -name default -type s 2>/dev/null | head -1)` then `t() { tmux -S "$TMUX_SOCKET" "$@"; }`. Drive with `t send-keys -t "session:window" "prompt" Enter` to send and `t capture-pane -t "session:window" -p -S -50` to read.
</socket_fails_silently>

<multiline_submits_early>
send-keys treats every newline as Enter, so a multi-line prompt submits mid-thought. Paste from a buffer without a submit, then send Enter once: `t load-buffer /tmp/prompt.md`, `t paste-buffer -t "session:window"`, `t send-keys -t "session:window" Enter`.
</multiline_submits_early>

<resume>
To continue a spawned session later, find its session id (shown in claude's status bar, and the name of its `.jsonl` transcript) and run `claude --resume <id>` in a fresh window.
</resume>

<oneshot_is_gated>
Headless `claude --print` runs and exits with no window, but a guard blocks it by default because interactive tmux sessions are the sanctioned path. For a genuinely sanctioned one-off, prefix the command with `CLAUDE_HEADLESS_SANCTIONED=1`.
</oneshot_is_gated>

<tmux_traps>
After `new-window` or `new-session -d` the target may not be ready instantly; verify with `list-windows`/`list-sessions` before sending keys, since "can't find session" means it raced. Pane index follows `pane-base-index`, so check `list-panes` before targeting a pane rather than assuming `0`. Stop a runaway with `C-c` and no Enter, repeated if needed. Add `-J` to `capture-pane` when wrapped lines come back garbled.
</tmux_traps>
