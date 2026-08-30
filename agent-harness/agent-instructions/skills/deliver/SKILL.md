---
name: deliver
description: Drive a software goal end-to-end: investigate context, design the build process, author a goal prompt, then execute with workflows and subagents until it works live. For big objectives needing a process, not one-off tasks.
---

<core_authority>
Core `<evidence>`, `<autonomy>`, `<completion>`, `<delegation>`, `<context>`, and `<coding>` own the persistent defaults
used here. This skill composes them into the bounded process for delivering one large software goal.
</core_authority>

<scope>
Use this when the goal is large and multi-step enough that the right first move is to design a build process rather than
start coding: a feature program, a migration, remediating many findings, anything spanning several increments or
sessions. For a one-off task just do the task, because running this whole loop on a small change costs more than it
saves. The deliverable is working software with value banked at every step, never a plan that defers all value to a
big-bang finish.
</scope>

<understand_before_designing>
Investigation earns the right to commit to a build process; it is not a ceremonial phase boundary. Read the
authoritative material, map the relevant system, and verify the brief against reality instead of trusting it. Form an
initial design only after enough evidence exists to make it useful, keep that design provisional, and revise it when
implementation or new evidence materially changes the model. Never force repository discoveries into a stale brief or
plan merely because it was written first.
</understand_before_designing>

<design_the_process_from_context>
Derive the steps from this goal's context; never paste a fixed template. Build the regression safety net needed for the
risky paths, decompose into independently shippable vertical slices ordered by dependency and risk, and sequence them so
stopping after any slice still leaves the system better. Name invariants that must not weaken, identify irreversible or
owner-only decisions before execution reaches them, and define done-per-increment and value-per-milestone so completion
is objective.
</design_the_process_from_context>

<author_the_goal>
Persist the plan to a durable tracker before executing, using a deep-work workspace or the repository's equivalent, and
keep that tracker as the single source of live state. Then use the `goal-prompt` skill to write one self-contained
launch brief that points at the tracker instead of restating it, so the brief stays valid as the plan evolves.
</author_the_goal>

<human_gate_before_launch>
Launching the autonomous run is a human-only action: `/goal` is reserved for the human and the agent must never invoke
it, directly or through any tool. Do everything through the finished goal prompt and tracker, then stop at that hard
boundary and hand the human the launch brief. Execution resumes only after a human launches it.
</human_gate_before_launch>

<execute_incrementally>
Run each slice through one evidence loop. For a bug, establish the focused failing reproducer described by the coding
skill when the behavior can be represented faithfully; for new behavior, establish the smallest testable contract. Build
the smallest reversible diff for one concern, verify the evidence that distinguished the decision, ship one cohesive
commit, and update the tracker. Parallelize only independent breadth; do not use parallel agents to manufacture
confidence in the same favored solution.
</execute_incrementally>

<prove_it_live>
Value is real only when it runs, so carry verification as far toward the actual app, UI, integration, or end-to-end path
as the change and environment require. Never report done from an agent's self-report or a generated summary; inspect the
artifact and observed behavior, and let contradictory runtime evidence invalidate an earlier test or assumption.
</prove_it_live>

<discipline>
Keep every increment reversible enough that a bad slice can be backed out cleanly; surface owner-only or irreversible
decisions before crossing them; reuse the goal's shared primitives rather than forking parallel state; and keep the
tracker current so interruption resumes from durable evidence rather than reconstructed memory.
</discipline>
