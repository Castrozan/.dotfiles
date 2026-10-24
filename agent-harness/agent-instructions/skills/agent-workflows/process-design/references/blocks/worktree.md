---
block: worktree
group: memory
provides: isolation
needs: driver
---

### What it gives

A separate checkout per writer, so parallel agents change code without overwriting each other.

### Use when

Two or more agents write the same repository at once. Avoid it for read-only helpers.

### Instruction

Give each writer its own worktree and branch, and integrate through the driver's review and merge.

### Harness

Isolated worktrees for Claude Code subagents; git worktrees for peers.
