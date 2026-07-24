---
name: deliver
description: Drive a large software goal end-to-end - investigate context, design the build process, author a goal prompt, then execute with workflows and subagents until it works live. For big objectives needing a process, not one-off tasks.
---

<scope>
Use this when the goal is large and multi-step enough that the right first move is to design a build process rather than
start coding: a feature program, a migration, remediating many findings, anything spanning several increments or
sessions. For a one-off task just do the task, because running this whole loop on a small change costs more than it
saves. The deliverable is working software with value banked at every step, never a plan that defers all value to a
big-bang finish.
</scope>

<understand_before_designing>
Investigation is its own phase, finished before any design. Read the authoritative material in full, map the system, and
verify the brief against reality instead of trusting it: re-check each claim or anchor against the actual code and
record what drifted, because a plan built on a stale brief fixes the wrong thing. Do not propose a single step until you
understand the system.
</understand_before_designing>

<design_the_process_from_context>
Derive the steps from this goal's context; never paste a fixed template. Anchor the design on principles that
generalize: build the regression safety net first (the tests or gate that make every later change provably
non-regressing) so nothing regresses silently; decompose into independently-shippable vertical slices ordered by
dependency and risk; sequence so value banks at every merge and stopping after any slice still leaves the system better;
name the invariants that must never weaken and treat any change that erodes one as wrong by definition; identify the
irreversible or owner-only decisions and plan to surface them rather than decide them. Define done-per-increment and
value-per-milestone up front so completion is objective, not a matter of opinion.
</design_the_process_from_context>

<author_the_goal>
Persist the plan to a durable tracker before executing (a deep-work workspace or PLAN file per the `deep-work` skill) so
it survives compaction and resumes across sessions; that tracker is the single source of live state and you update it as
the last step of every increment. Then use the `goal-prompt` skill to write one self-contained launch brief that points
at the tracker as the live spec instead of restating it, so the brief stays evergreen as state changes.
</author_the_goal>

<human_gate_before_launch>
Launching the autonomous run is a human-only action: `/goal` is reserved for the human and the agent must never invoke
it, directly or through any tool. Treat it as a hard barrier: do everything up to and including authoring the goal
prompt and tracker, then stop, hand the human the finished one-line brief, and wait. The human pastes it into `/goal` to
start the run; the execution phases below resume only after a human has launched it, never on the agent's own
initiative.
</human_gate_before_launch>

<execute_incrementally>
Run each slice through one loop: write a failing repro or test first because red-before-green is the only proof the work
was needed and is done (`test` skill); build the smallest diff for one concern behind a reversible flag defaulted off;
verify; ship a small commit staged by name; update the tracker. Parallelize with the Workflow tool when work fans out
across many files, perspectives, or candidates, keeping its control flow deterministic; route coordinated multi-step
work to a Workflow and single read-only queries to a plain Agent subagent, never to Teams, per the delegation rules.
Flip a flag default-on only after its slice is green.
</execute_incrementally>

<prove_it_live>
Value is real only when it runs, so end every increment with the V-model carried up to a real run: unit, integration,
then the actual app, UI, or end-to-end path (`verify` skill), not unit tests alone. Never report done from an agent's
self-report or scraped output; prove it from observed live behavior, and review the artifact an agent produced before
trusting its claim of success.
</prove_it_live>

<discipline>
Keep every change reversible and flag-gated so a bad slice rolls back by a plain revert; surface owner and irreversible
decisions and never decide them unilaterally; reuse the goal's shared primitives and never fork a second parallel store
that drifts from the first; stage commits by name, never with `-A`; and keep the tracker current every increment so an
interrupted session resumes from disk rather than from re-explanation.
</discipline>
