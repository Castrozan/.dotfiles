---
block: dry-run
group: controls
provides: rehearsal
needs: action
---

### What it gives

The same composition executed with actions stubbed and gates simulated, producing a trace to compare against the drawing
before the real run.

### Use when

The design is accepted and the real run is costly or irreversible. Run it before the first real action.

### Instruction

Stub every side effect, feed recorded or synthetic observables, simulate each gate's answers, and compare the trace's
agents, loops, and gates against the drawing.

### Harness

Each script's dry-run mode; a LangGraph or workflow run against stubs.
