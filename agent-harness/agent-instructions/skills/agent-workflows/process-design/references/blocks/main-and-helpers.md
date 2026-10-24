---
block: main-and-helpers
group: agents
provides: driver, subagents, artifact
needs: goal, budget
---

### What it gives

The main agent keeps working on the critical path while subagents take defined side tasks with fresh contexts and return
condensed results.

### Use when

Side tasks would flood the main context with searches, logs, or dumps, and the helpers only read or own disjoint
outputs. Avoid it when helpers would edit the main agent's files, or when the task needs frequent back-and-forth that a
fresh context must rebuild every time.

### Instruction

Delegate only tasks already decided, each with a brief naming objective, output shape, tool guidance, and boundaries,
and say whether to wait for all. Give helpers the narrowest tools and the cheapest model that fits, have them write
bulky output to files and return references, and keep integration, judgment, and every side effect in the main agent.

### Pitfalls

Helpers lack the main agent's unstated decisions, so their writes conflict; every result costs main-context space; total
tokens exceed a single agent's run.

### Harness

Claude Code subagents with tools, model, isolation, background, and turn limits per definition; Codex worker and
explorer subagents under a concurrency cap; OpenCode task subagents.
