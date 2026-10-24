---
block: tracker
group: memory
provides: state
needs: driver
---

### What it gives

One durable file holding the plan, decisions, progress, monitors, and approvals, so the process survives context
compaction and restarts.

### Use when

The process outlives one context or has more than one actor. A short single-context task needs none.

### Instruction

Only the driver writes the tracker. Update it after every decision, action, and approval, and read it first after every
restart or compaction.

### Harness

A file in the task's deep-work workspace or the repository's equivalent.
