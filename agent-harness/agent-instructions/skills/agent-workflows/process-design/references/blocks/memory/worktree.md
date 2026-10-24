---
block: worktree
group: memory
provides: isolation
needs: driver, verdict
---

# worktree

### What it gives

A separate checkout per writer, so parallel agents change code without overwriting each other.

### Use when

Two or more agents write the same repository at once. Avoid it when writers would still share ports or databases
unisolated, or when the work is one monolithic task without a way to split it.

### Instruction

Give each writer its own worktree, branch, and runtime resources; keep worktrees short-lived; integrate one branch at a
time through the verifier, rebasing the next onto the result, because parallel building is fine and parallel merging is
not.

### Pitfalls

Worktrees prevent textual conflicts, not semantic ones; disk use grows with every checkout.

### Harness

Claude Code worktree sessions and subagent worktree isolation; git worktrees for peers.
