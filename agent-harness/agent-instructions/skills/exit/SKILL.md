---
name: exit
description: End the current Claude Code, Codex, or OpenCode session cleanly. Use when work is complete, committed where applicable, and the session should terminate.
---

<prerequisites>
All tasks complete. Changes committed if applicable. Summarize accomplishments.
</prerequisites>

<execution>
Run `agent-session exit`.
</execution>

<notes>
The command finds a supported harness only among its ancestors, reports the target, and terminates it with its direct
children. When no target is found, use the harness's own exit control instead of signaling an unrelated process.
</notes>
