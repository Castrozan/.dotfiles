---
name: deep-work
description: Persist task context to disk so big or compaction-prone work survives across sessions. Use for work over ~5 steps, spanning sessions, or when explicitly asked to preserve context; not for quick fixes.
---

<core_context_authority>
Core `<context>` owns what must survive likely context loss. This skill owns the bounded workspace layout, activation,
update, recovery, heartbeat, and cleanup procedure for work that needs durable continuity.
</core_context_authority>

<activation>
Activate when any condition is met: user says "big work" or similar, task has more than 5 discrete steps, work will
clearly span multiple sessions, or user explicitly asks to preserve context. Do not activate for quick fixes,
single-file edits, or tasks completable in one exchange. When the case is borderline, choose the lighter path unless
losing the current context would be meaningfully expensive; do not interrupt the user merely to decide whether to
activate an internal persistence mechanism.
</activation>

<workspace>
Create `.deep-work/{task-slug}/` in the project root. Add `.deep-work/` to `.gitignore` if not present. The workspace
contains four files with distinct purposes: `.deep-work/{task-slug}/prompts.md` stores every user prompt verbatim with
timestamps and is the source of truth for what was asked; `.deep-work/{task-slug}/plan.md` stores the current
provisional implementation plan with dependencies and phase state and changes whenever evidence changes the approach;
`.deep-work/{task-slug}/progress.md` is the chronological record of completed work, decisions, rationale, and files
changed; `.deep-work/{task-slug}/context.md` holds curated high-signal requirements, constraints, corrections,
dependencies, and decisions that cannot be cheaply rediscovered from the source. Do not duplicate raw dumps across
these files.
</workspace>

<update_cadence>
Write to disk immediately after a substantial user prompt, after each plan phase, whenever evidence changes the
approach, and before responding after significant work. Persist before a point where context loss would force expensive
reconstruction rather than writing continuously for ceremony.
</update_cadence>

<recovery>
On session start or after compaction, if a `.deep-work/` workspace contains active work, read the workspace before
continuing. Reconstruct the task from `.deep-work/{task-slug}/prompts.md`, current direction from
`.deep-work/{task-slug}/plan.md`, completed work from `.deep-work/{task-slug}/progress.md`, and non-recoverable findings
from `.deep-work/{task-slug}/context.md`. Never ask the user to repeat information already persisted there.
</recovery>

<heartbeat_integration>
HEARTBEAT.md remains the lightweight signal that work is active. For deep-work tasks it points to the workspace and
current phase; the workspace owns the detailed state.
</heartbeat_integration>

<compaction_survival_test>
Design the workspace so work can continue if conversation history disappears between any two turns. If a fresh agent
could not recover the goal, current plan, completed work, and material discoveries from disk, persist the missing state
before proceeding.
</compaction_survival_test>

<cleanup>
When work is delivered and confirmed complete, remove the workspace directory and clear HEARTBEAT.md. Do not accumulate
stale workspaces. Workspaces older than 48 hours with no recent progress entries get reported to the user; do not
silently resume or delete stale work.
</cleanup>
