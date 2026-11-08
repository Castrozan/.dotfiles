---
name: swarm
---

### Core swarm authority

Core [delegation](../../../../core-rules/core.md#delegation) decides that a change is swarmed. This chapter owns how:
the brief, the batches, the launch, the per-batch check, and the integration the lead keeps.

### When a swarm pays

Swarm a decided change only when it splits into pieces in disjoint files and a script can judge each piece. Here, eight
Haiku engineers refactored 48 functions across 46 files in 19 minutes for about $3. One lead doing that alone costs
several times more and bloats its context. A change touching one or two files, a shared interface, or an open design
choice stays with the lead.

### Brief once

Write one brief file every worker reads, then give each worker only its batch. State the objective and the exact
acceptance rule. Forbid editing unassigned files, changing public names or behavior, editing a recorded baseline, and
any staging, commit, stash, checkout, reset or restore. List the verification commands to run before reporting.

Ask for a report naming each assigned item before and after, the files changed, every check run with its result, and
what failed.

### Batch and launch

Split the work into batches with no file in two batches and a handful of items each. Launch every batch in one message
so they run in parallel. In Claude Code use `Agent` with `subagent_type` `software-engineer` and `model` `haiku`. More
than two spawns need a description starting `orchestrated:`. In Codex use `spawn_agent` with `agent_type`
`software-engineer`. In OpenCode use the task tool with `software-engineer`.

### Check every batch

Run the repository's own gates per batch first: its linter, scorer and the tests that exercise the batch's files. When
no gate can judge the change, write a temporary checker in the session scratchpad, never in the repository. Give its
command to the workers too. `swarm-batch-gate` runs check commands against every batch's files from a JSON map of batch
name to files. In a `--check` command, `{files}` expands to that batch's quoted files.

Compare old and new on the same inputs when a change must preserve behavior. `swarm-differential-check` runs each
`--check` command in a snapshot of a git revision and in the working tree, then reports any differing exit status or
stdout. Its `{files}` expands to the files modified since that revision. Make each check a throwaway driver calling the
edited code with fixed inputs, in any language. The snapshot holds only tracked files, so reach untracked dependencies
by absolute path.

### Integrate as the lead

A worker's report is evidence, not a verdict. Read the whole diff, rerun every gate yourself, and fix gaps that need
files outside a worker's batch. Send a failing batch back once with the exact failure; after a second failure, finish it
yourself. Commit once with every file named, then run the repository's review and push procedure.
