---
name: coding
description: Implement and evolve code safely through clean design, focused tests, measured performance, Git discipline, and worktree isolation. Use for coding, fixing, testing, committing, history, or parallel branch work.
---

<implementation>
Keep each change small, cohesive, and placed where its reason to change belongs. Use names that describe domain meaning,
one responsibility per function, narrow dependencies, guard clauses, and data types for values that travel together.
Resolve an uncertain boundary with `architecture` before adding implementation detail.
</implementation>

<dependencies>
Keep dependency direction explicit: policy depends on stable interfaces, infrastructure stays at the edge, and callers
receive only the capability they use. Extend behavior at the boundary that owns it rather than duplicating switches
across callers. Inject what varies and construct what is fixed.
</dependencies>

<abstraction>
Extract a shared rule only after repeated use proves it changes for the same reason. Do not couple separate decisions
because their current syntax resembles each other, and do not add compatibility layers when downstream callers can move
to the current interface.
</abstraction>

<performance>
Treat responsiveness, memory, CPU, process count, and network activity as product behavior, especially in local clients
and TUIs. Measure the changed path before optimizing, set a bounded resource expectation, avoid unbounded work in render
or polling paths, and prefer incremental updates over repeated whole-state recomputation.
</performance>

<verification>
Read `testing.md` before changing code. It owns test-first behavior, focused local verification, and the CI gate.
</verification>

<version-control>
Read `git.md` before staging, committing, or investigating history. Read `worktrees.md` before isolating parallel work.
Read `knowledge.md` for shared-index and worktree traps, and `history.md` when using `git-history`.
</version-control>
