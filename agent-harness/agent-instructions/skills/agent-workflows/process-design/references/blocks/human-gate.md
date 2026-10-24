---
block: human-gate
group: controls
provides: approval
needs: driver
---

### What it gives

A stop where the owner approves, chooses, or supplies a missing fact before the process continues.

### Use when

The next step is irreversible, owner-only, or outward facing: a production write, a message, a ticket transition. Avoid
gates on reversible steps, which train the owner to approve without reading.

### Instruction

Ask with the evidence the owner needs to decide, the exact action, and its blast radius. Proceed only on an explicit
yes, and record the approval in the tracker.

### Harness

A structured question to the user; an interrupt in LangGraph; a user task in BPMN.
