---
block: planner
group: agents
provides: goal
needs: driver
---

# planner

### What it gives

A separate exploration and planning step that turns the framing into an approved plan or spec with acceptance criteria,
which a fresh session then executes.

### Use when

The change is larger than one sentence of diff, touches unfamiliar code, or will be executed by other agents. Skip it
for small tasks, where the plan costs more than the work.

### Instruction

Explore read-only, interview the human for missing facts, and write the plan to a file with acceptance criteria per
item. Get the plan approved before any write, execute it from a fresh context, and replan when an item's evidence breaks
an assumption.

### Pitfalls

Planning overhead on small tasks; a plan that hides open questions instead of naming them.

### Harness

Claude Code plan mode and plan approval for teammates; a spec file executed by a new session; Magentic-One's task
ledger.
