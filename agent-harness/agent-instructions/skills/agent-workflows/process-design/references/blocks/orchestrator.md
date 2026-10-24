---
block: orchestrator
group: agents
provides: driver, artifact
needs: peer, state, budget
---

### What it gives

A main agent manages other main agents, each running its own composition, over agent-to-agent messages: it assigns work,
requests replies, chases silence, and integrates outcomes.

### Use when

Separate processes each need a long-lived agent with its own skills, plugins, machine, or owner, and must be coordinated
toward one outcome. Avoid it when subagents or one team would do, and when a worker needs the orchestrator's full
context, because peers exchange messages and artifacts, not traces.

### Instruction

Model each assignment as a task with a goal, the skills or plugins it uses, a done check, and a reply contract saying
what to report, when, and in which shape. Keep a ledger of every peer's assignment, state, last reply, and next expected
reply; prefer push or idle notifications to polling, chase a peer that misses its window, and escalate one that stalls
twice.

### Pitfalls

Inter-agent misalignment is the largest failure family in multi-agent systems; peers guess instead of asking for input;
message loops; a peer's message treated as human consent or as a configuration change.

### Harness

The `orchestrate` skill and cross-session messaging for local peers; the A2A protocol, whose task states include
input-required and whose follow-ups reference earlier tasks, for remote ones. Each peer is designed as its own
composition from this toolbox.
