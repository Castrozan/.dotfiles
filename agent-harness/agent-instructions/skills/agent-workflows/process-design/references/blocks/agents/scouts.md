---
block: scouts
group: agents
provides: finding
needs: subagents, budget
---

### What it gives

Read-only researchers fanned out over independent questions and joined when all return, so discovery costs wall-clock
time once instead of once per question.

### Use when

Discovery is breadth-first or a large codebase investigation whose noise should stay out of the writer's context. Avoid
it for a narrow question one agent answers in a few tool calls, or when answers build on each other incrementally.

### Instruction

Run three to five scouts, each with a distinct angle, explicit boundaries, read-only tools, and a timebox. Have each
return condensed findings with evidence, or write to a file and return its path. Cross-check claims before they reach
the plan, and carry every unanswered question forward as a named unknown.

### Pitfalls

Token spend grows with every scout; agents prefer content farms over primary sources; an unscoped investigate request
reads everything and concludes nothing.

### Harness

Explore subagents or a workflow parallel step in Claude Code; Codex explorer; OpenCode explore; ADK parallel agents with
distinct output keys.
