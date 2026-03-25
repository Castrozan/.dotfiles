<prerequisites>
Running inside tmux. Commit any pending changes before restarting.
</prerequisites>

<execution>
claude-restart "Continue from where you left off."
</execution>

<continuation>
The script accepts an optional first argument as a continuation prompt. When provided, after claude restarts and shows the input prompt, the script automatically types and submits that message. This lets you resume work without waiting for user input.

To restart without auto-continuing, call the script with no arguments:
claude-restart
</continuation>

<notes>
Discovers the current session ID from claude's /proc cmdline args (--resume or --session-id). Falls back to finding the most recently modified session jsonl in the project directory. Always uses `claude --resume <id>` — never `--continue`. Forks a detached process that waits for claude to die, then sends the resume command to the tmux pane. SessionStart hooks fire on resume, recovering deep-work context automatically.
</notes>
