---
block: context-handoff
group: memory
provides: handoff
needs: driver
---

### What it gives

A structured summary or an artifact reference passed between phases or agents, so the receiver keeps the decisions
without the noise.

### Use when

A phase ends, an agent hands work to another, or the context nears its limit. Pass artifacts by reference rather than
retelling them.

### Instruction

Write the handoff to a file with the goal, decisions and their reasons, modified files, commands that verify the work,
and open questions; maximize recall first, then trim. Start the next phase from that file in a fresh context.

### Pitfalls

Summaries drop implicit decisions; a wrong fact in a handoff does more harm than a missing one.

### Harness

Compaction steering in Claude Code instructions; note files; a spec executed by a fresh session; OpenCode's compaction
agent.
