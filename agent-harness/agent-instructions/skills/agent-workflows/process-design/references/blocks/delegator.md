---
block: delegator
group: agents
provides: driver, subagents
needs: none
---

### What it gives

The main agent only plans, delegates, integrates, and verifies, so its context stays small and clean for judgment across
a long or wide task.

### Use when

The work spreads across more units than one context can hold, and each unit fits one worker. Avoid it for small tasks,
where the brief costs more than doing the work.

### Instruction

Do no unit of work yourself. Hand each unit to a worker with a complete brief, track every unit in the tracker, verify
each result against its done check, and replan when progress stalls instead of retrying the same brief.

### Harness

Claude Code subagents or a workflow script for a fixed fan-out; Codex and OpenCode subagents with the main agent holding
joins and loops.
