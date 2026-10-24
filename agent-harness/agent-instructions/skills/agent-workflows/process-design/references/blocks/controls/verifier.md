---
block: verifier
group: controls
provides: verdict
needs: artifact
---

# verifier

### What it gives

An executable check, such as tests, a build, a linter, a fixture diff, or a live probe, that returns pass or fail with
no model judgment.

### Use when

Always, wherever an executable criterion exists: before reviewers, before waves, and before done. Fall back to reviewers
or the human only when no check can decide.

### Instruction

Make the check as close to perfect as possible, because the agent will solve whatever it measures. Verify end to end,
where the outcome is consumed rather than where it is written, keep its output short with details in a log, and gate the
agent's stop on it.

### Pitfalls

Unit tests or a single request standing in for an end-to-end check; checking that the write happened instead of that the
objective holds.

### Harness

Claude Code stop hooks and goal evaluation; CI; browser automation for end-to-end checks.
