---
block: script-monitor
group: eyes
provides: alarm
needs: observable
---

### What it gives

A deterministic watcher that reads an observable on a cadence and emits an event only when a threshold is crossed,
spending no model tokens while nothing is wrong.

### Use when

The threshold is exact: a queue size, an error rate, a count that stalls. This is the default watcher; add agents only
for judgment.

### Instruction

Run one monitor per signal, list every monitor in the tracker, give each an until condition, and never start a duplicate
of a running monitor.

### Harness

Claude Code Monitor and background commands; cron or a supervisor elsewhere.
