---
block: eval-gate
group: controls
provides: verdict
needs: trace
---

### What it gives

A versioned evaluation suite that gates changes to the process itself: its skills, briefs, composition, or models.

### Use when

The process recurs and will be changed over time, so a change can regress it silently.

### Instruction

Start from twenty to fifty tasks drawn from real failures, grade with code where possible and a model judge otherwise,
measure consistency across repeated runs as well as single success, and run the suite on every change to the process.

### Pitfalls

Evals written after the fact that only confirm the current behavior; a judge with the same blind spots as the agent.

### Harness

Repository evaluation suites run in CI; skill authoring that starts from evals; observability platforms that rerun
traces.
