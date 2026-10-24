---
block: script-monitor
group: eyes
provides: event
needs: observable
---

# script-monitor

### What it gives

A deterministic watcher that reads an observable and emits an event only when a threshold is crossed, spending no model
tokens while nothing is wrong.

### Use when

The trigger condition can be coded: tailing logs, watching CI or a queue, counting until a number stalls. This is the
default watcher; add agent eyes only for judgment.

### Instruction

Run one monitor per signal, emit one line per meaningful event because every line wakes the agent, filter noisy feeds,
give each an until condition, list every monitor in the tracker, re-arm at its deadline, and never start a duplicate of
a running monitor.

### Pitfalls

Monitors and background commands are lost on resume; some providers lack the monitor tool.

### Harness

Claude Code Monitor, plugin monitors, and channels for longer horizons; Codex asynchronous hooks; OpenCode plugin
events; cron or a supervisor elsewhere.
