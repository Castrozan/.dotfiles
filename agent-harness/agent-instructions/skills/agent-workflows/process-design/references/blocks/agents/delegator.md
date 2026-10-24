---
block: delegator
group: agents
provides: driver, subagents, artifact
needs: goal, budget, verdict
---

# delegator

### What it gives

The main agent only plans, delegates, integrates, and verifies, so its context stays small and clean for judgment across
a long or wide task.

### Use when

The work exceeds one context and its subtasks cannot be predicted in advance, such as breadth-first research or a large
split change. Avoid it when subtasks share heavy context, when the work is sequential, or when the integrator cannot
verify what comes back.

### Instruction

Do no unit of work yourself. Scale effort to the task with explicit rules, hand each unit a complete brief, and design
the report-back each worker owes. Save the plan to the tracker before the context fills, track every unit there, verify
each result against its done check, and replan when progress stalls instead of resending the same brief.

### Pitfalls

The lead starts implementing instead of waiting, or stops before every unit is done; workers assume state they were
never given; vague briefs duplicate work; token cost multiplies.

### Harness

Claude Code subagents or a workflow script for a fixed fan-out, or an agent team lead; Microsoft Agent Framework
Magentic orchestration; CrewAI hierarchical process; Camunda's AI agent over an ad-hoc sub-process.
