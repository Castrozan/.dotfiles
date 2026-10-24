---
block: consultant
group: agents
provides: finding
needs: driver
---

# consultant

### What it gives

A stronger model consulted for a hard decision while cheaper models carry the routine work, with every agent block
assigned a model tier by role.

### Use when

Most steps are narrow but a few decisions are ambiguous or high stakes. Escalation works best when the consulted model
is clearly stronger than the one asking.

### Instruction

Assign each agent block a model by difficulty: small models classify, extract, and format; the strongest model leads and
decides. Send a stuck or high-stakes decision to the consultant with the evidence gathered so far, and act on its
finding as advice, not authority.

### Pitfalls

Escalating everything erases the savings; a consultant without the evidence answers a different question.

### Harness

A per-subagent model setting in Claude Code, Codex, and OpenCode; model routers such as RouteLLM for automatic tiering.
