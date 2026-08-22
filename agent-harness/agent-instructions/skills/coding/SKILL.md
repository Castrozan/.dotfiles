---
name: coding
description: Implement and evolve code safely. Use for coding, fixes, tests, commits, Git history and archaeology, or parallel branch work.
---

<core-coding-authority>
The shared core `<coding>` section owns persistent defaults for naming, comments, cohesion, dependencies, precedent,
abstraction, workarounds, resource behavior, and verification. Apply it throughout coding work; use this skill only for
the bounded procedures and routes below.
</core-coding-authority>

<architecture-routing>
Read the `architecture` skill before choosing or moving a structural boundary, adding a module or service, changing
state or failure ownership, or introducing implementation detail whose correct owner is uncertain.
</architecture-routing>

<workaround-procedure>
After applying core `<coding>` to a workaround, identify the exact external limitation, name the boundary for what it
compensates for, expose only what consumers need, and keep it easy to test and delete. Let the repository and
`architecture` skill determine the concrete shape; a generic wrapper can hide the correct owner.
</workaround-procedure>

<performance-procedure>
After applying core `<coding>` to resource behavior, define the representative workload, metric, baseline, and bounded
expectation before optimizing. Compare the changed path before and after, and inspect render or polling paths for
unbounded work and repeated whole-state recomputation.
</performance-procedure>

<verification-routing>
Read `testing.md` before changing code. It owns the bounded reproducer, coverage, execution-order, and
delivery procedure; repository-local instructions may add stronger gates.
</verification-routing>

<version-control-routing>
Read `git.md` before staging, committing, or investigating history. Read `worktrees.md` before isolating parallel work.
Read `knowledge.md` for shared-index and worktree traps, and `history.md` when using `git-history`.
</version-control-routing>
