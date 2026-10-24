---
block: orchestrator
group: agents
provides: driver
needs: peer, state
---

### What it gives

A main agent manages other main agents, each running its own composition, over agent-to-agent messages: it assigns work,
requests replies, chases silence, and integrates outcomes.

### Use when

Separate processes each need a long-lived agent with its own skills, plugins, or machine, and must be coordinated toward
one outcome. Avoid it when subagents would do, because every peer is a full session with its own cost.

### Instruction

Give each peer one goal, the skills or plugins it uses, its done check, and its reply contract: what to report, when,
and in which shape. Keep a ledger of every peer's assignment, last reply, and next expected reply; chase a peer that
misses its reply window, and escalate one that stalls twice. Never let two peers own the same artifact.

### Harness

The `orchestrate` skill for cross-session peers; the A2A protocol or a local message bus for transport. Each peer is
designed as its own composition from this toolbox.
