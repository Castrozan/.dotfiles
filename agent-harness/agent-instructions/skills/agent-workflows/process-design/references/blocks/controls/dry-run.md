---
block: dry-run
group: controls
provides: rehearsal, trace
needs: action
---

# dry-run

### What it gives

The same composition executed with side effects stubbed and gates simulated, producing a trace of intended actions to
compare against the drawing before the real run.

### Use when

The design is accepted and the real run is costly or irreversible. When stubs would diverge from real tool behavior,
rehearse in a sandbox with real tools instead. Evidence for this block is still mostly vendor practice.

### Instruction

Stub every side-effecting system and seed disposable data, feed recorded or synthetic observables, simulate each gate's
answers, inspect the would-be tool calls, and compare the trace's agents, loops, and gates against the drawing.

### Pitfalls

Stubs hide schema drift and permission failures that only real systems reveal.

### Harness

Each script's dry-run mode; Claude Code plan mode for a read-only rehearsal of the reasoning; LangGraph breakpoints and
state edits.
