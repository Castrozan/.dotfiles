---
block: workflow-script
group: hands
provides: action, artifact
needs: driver, budget
---

### What it gives

A fixed fan-out, pipeline, or maker-checker loop executed by a script runner, with no model choice between steps and
schema-typed outputs.

### Use when

The steps are predictable or the same step runs over many items, beyond what one conversation can coordinate. Avoid it
across a human gate, because a started workflow takes no input, and where routing needs open-ended interpretation.

### Instruction

Type every step's output with a schema so code routes on it, try the workflow on a small slice before the full run,
retry per step instead of tuning prompts for bulk transforms, keep the script deterministic so it replays, and run one
workflow per segment between gates.

### Pitfalls

A mid-fan-out failure reruns later agents on relaunch; projected cost grows fast with item count.

### Harness

Claude Code dynamic workflows, which resume and cap concurrency; ADK sequential, parallel, and loop agents; LangGraph
graphs; Temporal and Mastra workflows. Codex and OpenCode run the same shape from the main agent.
