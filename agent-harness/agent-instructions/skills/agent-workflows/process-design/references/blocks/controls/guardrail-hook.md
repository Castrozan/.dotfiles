---
block: guardrail-hook
group: controls
provides: policy
needs: action
---

### What it gives

A deterministic check that blocks a forbidden action before it runs, whatever the model decides.

### Use when

A rule must hold every time with an exact predicate: no production write without approval, no secrets printed, no broad
staging. Avoid it for judgment calls, and never make it the only security boundary.

### Instruction

State the rule, its predicate, and its message; block before the tool runs, keep one hook per rewrite of a tool's input,
pair it with a sandbox for containment, and test that it blocks the forbidden call and allows the legitimate one.

### Pitfalls

Hosted tools can bypass hooks; post-tool hooks cannot undo; stop hooks that keep blocking are capped by the harness.

### Harness

Claude Code pre-tool hooks and permission rules; Codex hooks after trust review; OpenCode plugins that throw before
execution; agent SDK guardrails.
