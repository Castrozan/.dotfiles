---
block: tracker
group: memory
provides: state
needs: driver
---

# tracker

### What it gives

One durable file holding the plan, decisions, progress, monitors, and approvals, so the process survives compaction and
restarts.

### Use when

The process outlives one context or has more than one actor. A short single-context task needs none.

### Instruction

Only the driver writes the tracker. Keep a progress log plus a structured list of items whose pass flag is the only
field agents flip, update it after every decision, action, and approval, commit it as a checkpoint where it lives in
git, and read it first after every restart or compaction.

### Pitfalls

Concurrent whole-file writes overwrite each other; stale status blocks dependents; sequential identifiers collide across
agents.

### Harness

A file in the task's deep-work workspace or the repository's equivalent; task tools in Claude Code; git-backed trackers.
