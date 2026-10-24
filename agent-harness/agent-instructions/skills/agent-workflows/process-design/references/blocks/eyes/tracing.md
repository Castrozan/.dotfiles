---
block: tracing
group: eyes
provides: trace
needs: driver
---

# tracing

### What it gives

Spans for every model call, tool call, handoff, and cost, so failures are diagnosed from what ran rather than from what
agents remember.

### Use when

The process runs unattended, in production, or across several agents, or an eval gate needs traces to grade.

### Instruction

Instrument every agent operation and handoff, record tokens and cost per agent, and keep traces outside any agent's
context so a failure stays diagnosable after compaction.

### Pitfalls

Harness support is uneven; traces that capture prompts can capture secrets.

### Harness

OpenTelemetry generative AI semantic conventions, which cover MCP; Phoenix and Langfuse backends; harness transcripts as
the fallback.
