---
name: coding
description: Implement and evolve code safely. Use for coding, fixes, tests, implicit state machine audits, commits, Git history and archaeology, or parallel branch work.
---

### Core coding authority

Core [design](../../../core-rules/core.md#design) and [coding](../../../core-rules/core.md#coding) own the persistent
defaults. Apply them throughout coding work; use this skill only for the bounded procedures and routes below.

### Architecture routing

Read the `architecture` skill before choosing or moving a structural boundary, adding a module or service, changing
state or failure ownership, or introducing implementation detail whose correct owner is uncertain.

### Performance procedure

Define the representative workload, metric, baseline, and bounded expectation before optimizing. Compare the changed
path before and after, and inspect render or polling paths for unbounded work and repeated whole-state recomputation.

### Verification routing

Read [testing](references/testing.md) before changing code. It owns the bounded reproducer, coverage, execution-order,
and delivery procedure; repository-local instructions may add stronger gates.

### Swarm routing

Read [swarm](references/swarm.md) before fanning a decided change out to parallel engineer agents. It owns the brief,
the batches, the per-batch check with the `swarm-batch-gate` and `swarm-differential-check` helpers, and integration.

### State machine routing

Read [state machines](references/state-machines.md) before auditing code for implicit state, or before turning flags,
markers and async phases into an explicit machine. It owns the audit, its report template, and the four-part design.

### Version control routing

Read [git](references/git.md) before staging, committing, or investigating history. Read
[worktrees](references/worktrees.md) before isolating parallel work. Read [knowledge](references/knowledge.md) for
shared-index and worktree traps, and [history](references/history.md) when using `git-history`.
