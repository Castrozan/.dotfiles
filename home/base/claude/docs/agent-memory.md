# Agent Memory

The memory system did not fail at retrieval. It failed at **tiering**: a per-fact index that grows `O(n)` in the always-on
tier will eventually outweigh every deliberately authored instruction surface, and it did. This document records what
broke, why the fix is a filing discipline rather than a subsystem, and what replaces it.

## What broke

Measured on kira, 2026-07-30, before removal:

| Surface | Bytes | Always-on | Reviewed |
|---|---|---|---|
| `~/.claude/CLAUDE.md` (assembled from `agents/core_rules/`) | 12665 | yes | yes |
| `.dotfiles/CLAUDE.md` | 9155 | yes | yes |
| `~/.claude/projects/-Users-lucas-zanoni--dotfiles/memory/MEMORY.md` | **19008** | yes | **no** |

The memory index was the largest always-on surface in any session in this repo, 1.5x the global `CLAUDE.md`, and the only
one that was never budgeted, never reviewed, and grew monotonically. In `~/repo/ai-first-initiative` the same index was
18006 bytes across 61 entries.

Nineteen separate stores existed, 445 files total. Three of them belonged to the same agent (`~/clawde/steward`,
`~/clawde/steward/state`, `~/clawde/steward/memory`), created because that agent's working directory drifted. One belonged
to a git worktree, cut off from its own parent repository's store. Three belonged to sessions launched from `$HOME`.

## The five structural defects

**A flat per-fact index is `O(n)` and always-on.** Every memory contributes a line whether or not the session touches its
subject. No writing discipline fixes this: 112 perfect fifteen-word hooks still cost ~2200 tokens, and 300 facts cost
6000. Only hierarchy scales, and the index had none.

**Index entries drift from pointer to payload.** The contract says one line, a hook, never content. In practice entries
reached fifty words carrying the conclusion itself: MR numbers, custom field ids, and cross-project assertions. One
`ai-first-initiative` entry fused `aplicacoes-atendimento-triage` with `betha-ai-maintainer` in a single sentence, loaded
unconditionally into every session in that repo. That is the observed context bleed. The index had become a second,
always-on copy of the store it was supposed to route to.

**Store identity was an accident of the working directory.** The store key is the encoded absolute `cwd`. A subject is not
a directory: launching from a subdirectory, a worktree, or `$HOME` forks the store.

**The most valuable facts were the least shared.** `no-employer-names-in-public-repos`, `finish-the-merge-dont-hand-it-back`
and the delivery-process entry are global working agreements, yet they lived only in the dotfiles store and were invisible
from every other repository. Conversely, facts about `lucaszanoni-web` and the arr stack sat in the dotfiles store purely
because that is where the session happened to start.

**The type taxonomy carried no signal.** Seventy of 112 dotfiles memories were typed `project`, including the AMFI tmux
kill, the destructive herdr chord, the arr stack topology and the delivery process. None are in-flight work. The taxonomy
offered no category for "durable trap learned by debugging", which is the dominant real class, so everything fell into
`project`. A type field that cannot separate durable knowledge from live work state cannot drive a tiered injection
pipeline, which is precisely what the design called for.

## Knowledge is not work state

These are opposite objects and merging them is the root category error.

Knowledge is slow-changing, cross-session, cumulative, small per item, and safe to broadcast. Work state is fast-changing,
scoped to one task, disposable, large, and poison to broadcast: injected into a different session it reads as "here is your
current task", which is exactly the failure that was reported.

Work state already has a home. `HEARTBEAT.md` covers quick tasks and `.deep-work/*/PLAN.md` covers long ones; both are
scoped to the task rather than the directory, and the SessionStart hook already restores them after compaction. Memory
holds knowledge only. Nothing dated, nothing in-flight, nothing that will be false next week.

## The design: facts live with their owner

There is no memory subsystem. A fact is filed against whatever already owns its subject, and that owner's existing loading
semantics do the tiering for free.

**A behavioral rule goes to `agents/core_rules/`.** If the fact is "always do X" or "never do Y", it is an instruction, not
an observation, and it belongs in the always-on tier that is already budgeted and reviewed. Roughly six current memories
qualify.

**A fact about a system goes to the skill that owns that system**, in a `knowledge.md` sibling of its `SKILL.md`. The skill
description is the router line and it is already paid for in the always-on budget; the body loads only when the session
touches the domain. This is the eager-description, lazy-body split the original design named as its model, and this repo
already demonstrates the router-plus-siblings pattern in the `instructions` skill.

**A fact about a repository goes to that repository's `CLAUDE.md`.** Colocating a fact with the artifact it describes is the
tightest possible scoping: it loads exactly when relevant, versions with the code, and dies when the code dies.

**A work-sensitive fact goes to `private-config`**, which is already private, synced and nix-deployed.

The 112 dotfiles memories map onto existing owners almost completely: 13 to the `nix` skill, 13 to `desktop`, 7 to
`git` and `worktrees`, 6 to `herdr`, and the arr entries to `arr-stack`. Two gaps remain, and they are the loudest signal in
the data: 29 facts about the clawde fleet and 18 about Claude Code harness behavior have no owning skill at all. Those
skills should exist regardless of memory. Eight entries describe other repositories and move out to them.

## Consequences

Always-on cost falls from ~4750 tokens to zero. Routing is carried by skill descriptions that are already loaded and
already reviewed, so the marginal always-on cost of the entire corpus is nothing.

Git becomes the provenance layer. The store had an `originSessionId` pointing at a transcript that may no longer exist;
version control gives blame, history, review, cross-machine sync and rollback instead, and `git log -S` finds both the fact
and the change that taught it.

Every write passes the repository gate. The store rotted because no write was ever reviewed. A knowledge edit is exactly as
consequential as a skill edit and now runs the same sequence, and it usually rides along with the change that produced the
lesson.

## Capture

Gate friction at the moment of discovery is fatal, so capture is separated from filing. An agent that learns something
mid-task appends it to `~/.claude/knowledge-inbox.md`, which is untracked, per-machine, and never loaded into context. The
`housekeeping` skill drains it, filing each entry against its owner or discarding it. Only the filed form is ever read.

## Write contract

Record a fact only if a competent agent would not re-derive it from the code in five minutes. Traps that leave no trace in
the source qualify: AMFI killing a running binary after a store swap, a locale-dependent window-title separator, a tool
that silently skips symlinked files. Anything the code states plainly does not.

One fact per entry, two to five lines, naming the observable symptom and the invariant behind it. No line numbers, no
dates unless the fact is genuinely time-bounded, no wikilink graph: adjacency inside a domain file is the link. A
`knowledge.md` entry is an observation, never a rule. If it starts prescribing, it belongs in `core_rules/`. Facts age, so
an entry naming a file, function or flag is verified against the tree before it is acted on.

## Guard

One check, and it is a test rather than a runtime mechanism: assert a byte ceiling on the assembled always-on surface, and
a ceiling on any single skill body that forces the router-plus-siblings split before a body gets heavy. This is the forcing
function the previous design lacked, and it is the only new code the design requires.

## Explicitly rejected

A per-fact always-on index, for the `O(n)` reason above. An automatic recall hook that injects file bodies on tool events:
the removed one ranked by raw ripgrep match count with no length normalization, shipped five full files per event, and
charged only the path string against its budget, but even a correct implementation is the wrong shape, since guessing
relevance from a tool call is strictly worse than a skill description the model reads and chooses. Working-directory-keyed
stores. Cross-agent store sharing by symlink. A dedicated write CLI and its telemetry, which is maintained code doing what
one `Write` call and one review already do. `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` stays set, since without it the harness
recreates both the cwd-keyed stores and the always-on index.

## Migration

No big-bang triage. The stores are inert with auto-memory disabled, so they remain on disk as a grep-able archive that
nothing loads, and there is no correctness pressure to convert them. Filing is incremental: create the two missing skills,
then graduate a fact into its owner the next time work touches that area. A single bounded pass over the 112 dotfiles
entries is worthwhile because that store carries this repo's hard-won traps; the other seventeen stores can age out
untouched.
