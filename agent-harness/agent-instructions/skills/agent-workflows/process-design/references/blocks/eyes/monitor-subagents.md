---
block: monitor-subagents
group: eyes
provides: watch, finding
needs: subagents, observable
---

# monitor-subagents

### What it gives

Subagents that watch the running processes and diagnose what they see, keeping log reading and triage out of the main
context.

### Use when

Telling a real regression from known noise needs judgment. Prefer waking them on a script monitor's event over a short
polling loop, since no evidence shows a polling agent watcher beats a script monitor with an escalation agent; poll only
when no signal can be coded.

### Instruction

Brief one watcher per concern with its signals, baseline of known noise, thresholds, cadence, and exit, written before
the run. A watcher reports and diagnoses; only the driver pauses, acts, or escalates.

### Pitfalls

Each polling turn costs a full model call; monitors stop when their parent subagent stops; watchers briefed at runtime
collect scope changes one message at a time.

### Harness

Claude Code background subagents messaged or spawned by the main agent when a monitor fires; Codex subagents.
