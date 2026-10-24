---
block: main-and-helpers
group: agents
provides: driver, subagents
needs: none
---

### What it gives

The main agent keeps working on the critical path while subagents take defined parallel tasks with fresh contexts and
return condensed results.

### Use when

Some tasks are independent of the main line and parallelize cleanly, such as research, lookups, or reviews, while the
main agent's own work cannot wait for them. Avoid it when helpers would write the same artifacts as the main agent.

### Instruction

Delegate only tasks already decided, each with a brief naming objective, inputs, output shape, allowed tools, budget,
and stop condition. Keep integration, judgment, and every side effect in the main agent, and treat helper output as
evidence to verify.

### Harness

Claude Code background subagents; Codex spawned agents up to its concurrency cap; OpenCode task subagents.
