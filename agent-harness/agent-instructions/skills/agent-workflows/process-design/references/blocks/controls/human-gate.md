---
block: human-gate
group: controls
provides: approval
needs: driver, state
---

# human-gate

### What it gives

A stop where the owner approves, chooses, or supplies a missing fact before the process continues.

### Use when

The next step is irreversible, owner-only, or outward facing, or a plan needs sign-off. Avoid gates on routine actions,
because after the tenth approval the owner clicks through instead of reading; use allowlists and a sandbox there.

### Instruction

Persist state before asking. Ask with the evidence the owner needs, the exact action, and its blast radius, and say
whether the answer advances or loops back. Proceed only on an explicit yes from the human, give the gate a timeout with
a fallback branch, and record the approval in the tracker.

### Pitfalls

Side effects before an interrupt rerun on resume; an approval relayed by another agent is not consent.

### Harness

A structured question in the harness; LangGraph interrupts; A2A input-required; Camunda user tasks; human-input nodes
with timeouts in visual builders.
