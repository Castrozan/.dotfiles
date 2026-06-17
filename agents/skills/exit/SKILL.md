---
name: exit
description: End the current Claude Code session cleanly. Use when all work is complete and committed and the session should terminate.
---

<prerequisites>
All tasks complete. Changes committed if applicable. Summarize accomplishments.
</prerequisites>

<execution>
claude-exit
</execution>

<notes>
Script verifies parent is 'claude' before sending SIGTERM. Fallback: tell user to type /exit or press Ctrl+D.
</notes>
