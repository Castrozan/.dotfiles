---
block: peer-session
group: agents
provides: peer
needs: goal
---

### What it gives

A long-lived interactive session in its own visible terminal pane, which the human can watch and steer, instead of a
hidden subagent.

### Use when

A worker must outlive the main context, run on another harness or machine, stay visible for the human, or talk directly
with other peers. Avoid it when only the result matters, since a subagent returns a summary for less.

### Instruction

Start each peer with task-specific context, because the lead's history does not carry over, plus its goal, its file
ownership, and its pre-approved permissions. Name it and address it by name, read its pane or transcript before
messaging it, and never type into a pane the human is using. Start with three focused peers rather than five scattered
ones.

### Pitfalls

In-process teammates are not restored on resume; stale task status blocks dependents; peers left unattended drift.

### Harness

Herdr panes through the `orchestrate` skill; Claude Code agent teams and background sessions; OpenCode child sessions.
