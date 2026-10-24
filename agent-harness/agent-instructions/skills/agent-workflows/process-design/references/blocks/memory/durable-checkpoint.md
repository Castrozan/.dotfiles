---
block: durable-checkpoint
group: memory
provides: state
needs: driver
---

### What it gives

Resumption from the last completed step after a crash, rate limit, or deploy, with bounded retries per step.

### Use when

Steps are expensive or the process runs long enough to be interrupted. Every retried step must be idempotent.

### Instruction

Mark each step boundary as a checkpoint, give every side effect an idempotency key, retry with a cap and a backoff, and
resume instead of restarting.

### Pitfalls

Retries repeat side effects that were not idempotent; a replay reruns everything after the first changed step.

### Harness

Claude Code workflow resume; LangGraph checkpointers; Temporal activities with retry policies; Camunda process state.
