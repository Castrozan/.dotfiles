---
block: canary-and-waves
group: controls
provides: rollout
needs: action, verdict, event, approval
---

### What it gives

A staged rollout: apply the action to a small canary, verify the outcome end to end, then proceed in throttled waves
with a resumable log, pausing on events and resuming when they clear.

### Use when

An action is bulk or irreversible, or a changed agent or process is being deployed. Skipping the canary turns a defect
in the write path into a defect in every record.

### Instruction

Size the canary and the wave rate up front, and make the canary representative rather than the easy items. Verify it
where the outcome is consumed, repair and rerun it at most twice, gate the first wave on the owner's approval, split the
run into steps so per-step failures show, pause on any event, and resume from the log.

### Pitfalls

An easy first wave hides the hard tail; a verifier that checks the write instead of the read path.

### Harness

The action script's batch and rate options plus a script monitor on the shared resource; Claude Code workflows pause and
relaunch with cached completed agents.
