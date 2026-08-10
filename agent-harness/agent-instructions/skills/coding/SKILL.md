---
name: coding
description: Implement and evolve code safely through clean design, focused tests, measured performance, Git discipline, and worktree isolation. Use for coding, fixing, testing, committing, history, or parallel branch work.
---

<implementation>
Keep each change small, cohesive, and placed where its reason to change belongs. Use names that describe domain meaning,
never abbreviate merely to save characters, keep one responsibility per function or script, prefer guard clauses, and
use data types for values that travel together. Add no comments, docstrings, section banners, commented-out code, or
TODO notes; names and structure carry the explanation. Legacy comments do not license new ones. Follow existing patterns
when they fit the established problem and constraints; existing code is evidence of local convention, not proof of good
design, so do not propagate a pattern merely because it already exists. Resolve an uncertain structural boundary with
`architecture` before adding implementation detail.
</implementation>

<dependencies>
Keep dependency direction explicit: policy depends on stable interfaces, infrastructure stays at the edge, and callers
receive only the capability they use. Extend behavior at the boundary that owns it rather than duplicating switches
across callers. Inject what varies and construct what is fixed. Group related files by domain when the repository's
structure permits it rather than flattening one domain into siblings distinguished only by repeated prefixes or
suffixes.
</dependencies>

<abstraction>
Extract a shared rule only after repeated use proves it changes for the same reason. Do not couple separate decisions
because their current syntax resembles each other, and do not add compatibility wrappers, deprecated aliases,
re-exports, generalized extension points, or speculative infrastructure when downstream callers can move to the current
interface. Prefer the smallest intervention that satisfies the actual constraints, where smallest means least
unnecessary system complexity and future change burden rather than fewest edited lines or files. Add a feature flag,
config gate, or environment switch only when the user asks or rollout safety genuinely requires one.
</abstraction>

<workarounds>
Isolate code that exists only to compensate for an external limitation so the rest of the system does not absorb that
limitation. Put the workaround behind one narrow boundary named for what it compensates for, expose only what consumers
need, and keep it easy to test and delete when the upstream constraint disappears. The repository and architecture skill
decide the concrete shape; do not impose a generic wrapper pattern when the local design has a better owner.
</workarounds>

<performance>
Treat responsiveness, memory, CPU, process count, and network activity as product behavior, especially in local clients
and TUIs. Measure the changed path before optimizing, set a bounded resource expectation, avoid unbounded work in render
or polling paths, and prefer incremental updates over repeated whole-state recomputation.
</performance>

<verification>
Read `testing.md` before changing code. It owns test-first behavior, focused local verification, and the delivery gate;
repository-local instructions may add stronger verification requirements.
</verification>

<version-control>
Read `git.md` before staging, committing, or investigating history. Read `worktrees.md` before isolating parallel work.
Read `knowledge.md` for shared-index and worktree traps, and `history.md` when using `git-history`.
</version-control>
