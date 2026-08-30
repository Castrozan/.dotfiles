---
name: coding
description: Implement and evolve code safely. Use for coding, fixes, tests, commits, Git history and archaeology, or parallel branch work.
---

<core_coding_authority>
The shared core `<coding>` section owns persistent defaults for naming, comments, cohesion, dependencies, precedent,
abstraction, workarounds, resource behavior, and verification. Apply it throughout coding work; use this skill only for
the bounded procedures and routes below.
</core_coding_authority>

<architecture_routing>
Read the `architecture` skill before choosing or moving a structural boundary, adding a module or service, changing
state or failure ownership, or introducing implementation detail whose correct owner is uncertain.
</architecture_routing>

<workaround_procedure>
After applying core `<coding>` to a workaround, identify the exact external limitation, name the boundary for what it
compensates for, expose only what consumers need, and keep it easy to test and delete. Let the repository and
`architecture` skill determine the concrete shape; a generic wrapper can hide the correct owner.
</workaround_procedure>

<performance_procedure>
After applying core `<coding>` to resource behavior, define the representative workload, metric, baseline, and bounded
expectation before optimizing. Compare the changed path before and after, and inspect render or polling paths for
unbounded work and repeated whole-state recomputation.
</performance_procedure>

<verification_routing>
Read `references/testing.md` before changing code. It owns the bounded reproducer, coverage, execution-order, and
delivery procedure; repository-local instructions may add stronger gates.
</verification_routing>
<version_control_routing>
Read `references/git.md` before staging, committing, or investigating history. Read `references/worktrees.md` before
isolating parallel work.
Read `references/knowledge.md` for shared-index and worktree traps, and `references/history.md` when using
`git-history`.
</version_control_routing>
