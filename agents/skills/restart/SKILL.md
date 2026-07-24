---
name: restart
description: Restart the current Claude Code session in place, resuming the same session with an optional continuation prompt. Use to reload after config changes or resume work without waiting for input.
---

<prerequisites>
Running inside herdr or tmux. Commit any pending changes before restarting.
</prerequisites>

<execution>
claude-restart "Continue from where you left off."
</execution>

<continuation>
The script accepts an optional first argument as a continuation prompt. When provided, after claude restarts and shows
the input prompt, the script automatically types and submits that message. This lets you resume work without waiting for
user input.

To restart without auto-continuing, call the script with no arguments:
claude-restart
</continuation>

<notes>
Discovers the current session ID from the claude process cmdline (--resume or --session-id), read via ps so it works on
darwin and Linux alike. Falls back to the most recently modified session jsonl in the project directory, and to `claude
--continue` when no id is found. Detects the enclosing multiplexer (herdr when `HERDR_PANE_ID` is set, else tmux), forks
a detached process that waits for claude to die, then drives the resume command back into the same pane through that
multiplexer. SessionStart hooks fire on resume, recovering deep-work context automatically.
</notes>
