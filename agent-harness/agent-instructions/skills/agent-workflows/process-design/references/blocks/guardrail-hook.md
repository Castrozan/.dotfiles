---
block: guardrail-hook
group: controls
provides: policy
needs: action
---

### What it gives

A deterministic check that blocks a forbidden action before it runs, whatever the model decides.

### Use when

A rule has an exact predicate: no production write without approval, no secrets printed, no broad staging. Prefer it to
an instruction whenever the predicate can be coded.

### Instruction

State the rule, its predicate, and its message, and test that the hook blocks the forbidden call and allows the
legitimate one.

### Harness

Pre-tool hooks and permission rules in Claude Code; equivalent hooks or sandbox policies elsewhere.
