<tmux_sessions>
Launch a Claude Code instance in a tmux window. The session is fully interactive — the user can watch, take over, or follow up at any time. Use the spawn script from this skill's `claude-scripts/` directory to create the window and optionally send an initial prompt.

Run `spawn-claude.sh --help` for exact syntax and flags. The script creates a named tmux window, starts claude in it, and optionally sends an initial prompt from a string or file.

After spawning, interact with the session through tmux primitives:

Send a follow-up prompt:
`tmux send-keys -t "session:window" "your prompt here" Enter`

Read current output:
`tmux capture-pane -t "session:window" -p -S -50`

The session persists independently — if the spawning agent's conversation ends, the tmux window and its claude instance remain alive for the user.
</tmux_sessions>

<one_shot>
For tasks with clear success criteria that need no interaction, use `claude --print` directly. It runs, prints the result, and exits — no tmux window, no back-and-forth. Pipe input or pass the prompt as an argument. Combine with `--dangerously-skip-permissions` for fully autonomous execution in trusted environments.
</one_shot>

<builtin_agents>
Claude Code has a built-in Agent tool for in-process delegation. For single-purpose read-only queries (research, codebase exploration, file search), use bare Agent tool — no tmux needed. For multi-agent implementation work with coordination needs, use Teams (TeamCreate) with `isolation: "worktree"` for code-editing teammates.

Choose tmux sessions over builtin agents when: the user needs to see or take over the work, the task benefits from a persistent interactive session, or you want the session to outlive your own conversation.
</builtin_agents>

<traps>
Multiline prompts via send-keys: tmux interprets Enter literally, so a newline in your string submits mid-prompt. For multi-line input, write the prompt to a temp file and use the spawn script's `--file` flag, or use `tmux load-buffer /tmp/prompt.md && tmux paste-buffer -t "session:window"` to paste without triggering Enter.

Session identification: the session ID appears in claude's status bar. Capture it with `tmux capture-pane` and grep for `.jsonl` if you need to resume later with `claude --resume <id>`.
</traps>
