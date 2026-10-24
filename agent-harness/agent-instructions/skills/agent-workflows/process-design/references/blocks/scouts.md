---
block: scouts
group: agents
provides: findings
needs: subagents
---

### What it gives

Read-only researchers fanned out over independent questions, joined when all return, so discovery costs wall-clock time
once instead of once per question.

### Use when

Discovery splits into independent open questions. Avoid it for one question, which one agent answers better without the
join overhead.

### Instruction

Give each scout one question, read-only access, a timebox, and an output of findings with evidence. Join on all scouts
or on the timebox, and carry every unanswered question into the plan as a named unknown.

### Harness

Explore or research subagents in Claude Code; a workflow script when the fan-out shape is fixed.
