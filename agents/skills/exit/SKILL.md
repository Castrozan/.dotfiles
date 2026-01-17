---
name: exit
description: Safely terminate the current Claude Code session. Use when user explicitly asks to end session.
---

# Exit Skill

Terminate ONLY this Claude session without affecting others.

## Prerequisites

Before running:
1. All tasks complete
2. Changes committed (if applicable)
3. Summarize what was accomplished

## Execution

```bash
claude-exit
```

The script verifies parent is 'claude' before sending SIGTERM.

## Fallback

If script fails, tell user to type `/exit` or press `Ctrl+D`.
