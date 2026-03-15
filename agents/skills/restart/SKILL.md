---
name: restart
description: Auto-restart the current Claude Code session. Use when context is stale, session needs a fresh reload, or user explicitly asks to restart. Requires tmux.
---

<prerequisites>
Running inside tmux. Commit any pending changes before restarting.
</prerequisites>

<execution>
claude-restart
</execution>

<notes>
Discovers the current session ID from the most recently modified .jsonl file, forks a detached process that waits for claude to die, then sends `claude --resume <session-id>` to the tmux pane. The SessionStart hooks fire on resume, recovering deep-work context automatically.

If not in tmux, falls back to telling the user to manually run `claude --continue`.
</notes>
