---
block: budget
group: controls
provides: budget
needs: driver
---

# budget

### What it gives

Ceilings on turns, iterations, tokens, cost, time, and agent count, each with defined behavior when hit.

### Use when

Always: every loop and every agent block needs one, because agents unaware of their termination conditions are a leading
cause of multi-agent failure.

### Instruction

Set a ceiling per loop and per agent block, name what happens at the ceiling, which is pausing into a human gate or
ending in a report, and record spend in the tracker so the human sees it.

### Pitfalls

A ceiling with no fallback stalls silently; a ceiling set after the run starts.

### Harness

Subagent turn limits in Claude Code, steps in OpenCode, turn and spend limits in the Claude Agent SDK, workflow agent
caps.
