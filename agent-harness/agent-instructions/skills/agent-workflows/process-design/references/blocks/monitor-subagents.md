---
block: monitor-subagents
group: eyes
provides: watch
needs: subagents, observable
---

### What it gives

Subagents watch the running processes and report breaches with a diagnosis, keeping watch noise out of the main context.

### Use when

Signals need judgment, such as telling a real regression from known noise. Pair them with a script monitor so they wake
on alarms instead of polling.

### Instruction

Brief one watcher per concern with its signals, baseline of known noise, thresholds, cadence, and exit, written before
the run. A watcher reports and diagnoses; only the driver pauses, acts, or escalates.

### Harness

Claude Code subagents messaged or spawned by the main agent when a monitor fires.
