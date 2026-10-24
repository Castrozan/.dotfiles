---
block: canary-and-waves
group: controls
provides: rollout
needs: action, watch, approval
---

### What it gives

A staged rollout: apply the action to a small canary, verify the outcome end to end, then proceed in throttled waves
with a resumable log, pausing on alarms and resuming when they clear.

### Use when

An action is bulk or irreversible. Skipping the canary turns a defect in the write path into a defect in every record.

### Instruction

Size the canary and the wave rate up front. Verify the canary where the outcome is consumed, repair and rerun it at most
twice, and gate the first wave on the owner's approval. Pause waves on any alarm and resume from the log.

### Harness

The action script's batch and rate options plus a script monitor on the shared resource.
