---
name: coding
description: Implement and evolve code safely. Use for coding, fixes, tests, commits, Git history and archaeology, or parallel branch work.
---

### Core coding authority

The shared core [coding](../../../core-rules/core.md#coding) section owns persistent defaults for naming, comments,
cohesion, dependencies, precedent, abstraction, workarounds, resource behavior, and verification. Apply it throughout
coding work; use this skill only for the bounded procedures and routes below.

### Architecture routing

Read the `architecture` skill before choosing or moving a structural boundary, adding a module or service, changing
state or failure ownership, or introducing implementation detail whose correct owner is uncertain.

### Workaround procedure

After applying core [coding](../../../core-rules/core.md#coding) to a workaround, identify the exact external
limitation, name the boundary for what it compensates for, expose only what consumers need, and keep it easy to test and
delete. Let the repository and `architecture` skill determine the concrete shape; a generic wrapper can hide the correct
owner.

### Performance procedure

After applying core [coding](../../../core-rules/core.md#coding) to resource behavior, define the representative
workload, metric, baseline, and bounded expectation before optimizing. Compare the changed path before and after, and
inspect render or polling paths for unbounded work and repeated whole-state recomputation.

### Verification routing

Read [testing](references/testing.md) before changing code. It owns the bounded reproducer, coverage, execution-order,
and delivery procedure; repository-local instructions may add stronger gates.

### Version control routing

Read [git](references/git.md) before staging, committing, or investigating history. Read
[worktrees](references/worktrees.md) before isolating parallel work. Read [knowledge](references/knowledge.md) for
shared-index and worktree traps, and [history](references/history.md) when using `git-history`.
