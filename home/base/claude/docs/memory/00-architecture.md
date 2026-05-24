# Memory architecture for persistent agents (and beyond)

Brainstorm capture, not final. Living doc - update as decisions land.

## Why this exists

`agents/skills/instructions/memory.md` says memory is "planned injection
pipeline + discovery procedure + behavioral contract." Three pillars, all
required. Discord bots (silver, future) need this first, but the design
must generalize to any Claude session that has a memory dir.

## Decisions made

### 1. Loading semantics

`MEMORY.md` loads ONCE per Claude process boot, not per inbound message.
Silver's process runs for days, so the in-context copy goes stale the
moment something is written. Reload triggers: process restart, daily
rotation, `/compact`, or an explicit `Read`. Implication: agent cannot
"scan MEMORY.md each turn" reliably - we cannot depend on it seeing its
own fresh writes mid-session. Discovery must be external (the recall
hook), not behavioral.

### 2. Index size

No artificial entry cap. The harness budget is 200 lines / 25KB for
`MEMORY.md`. Tell the agent to manage its own index: keep one-line
pointers, push detail into topic files, consolidate when approaching the
budget. Self-managed, periodic compaction.

### 3. Discovery via tool-use hook (GLOBAL, not bot-specific)

Hook fires on `PreToolUse` (every Claude session, not just persistent
agents). Script ripgreps the active memory dir using keywords from the
current prompt + tool args, emits `Recall: @path1 @path2 ...` when matches
score above threshold. Debounce: per-session state file caps recall to
once per N seconds and skips if keywords match last fire. Cost: ripgrep
is sub-ms; output is silent when no hits. Generalizes - any agent with a
memory dir gets associative recall for free.

### 4. Writes via shared CLI

One system-wide `memory-write` binary. Target dir is derived from cwd, not
passed - the agent cannot accidentally write into another agent's memory.
Validates length and format, dedupes against existing entries, appends
with ISO date + author, updates the matching one-line `MEMORY.md` pointer
in the same transaction. Optional LLM-check ("is this durable?") behind a
flag. Agent is instructed: never `Write`/`Edit` files under `memory/`,
always use `memory-write`. Garbage is prevented at the gate.

### 5. Runtime protocol lives in the discord-channel module

`agents/skills/instructions/memory.md` is the meta-stance for agents that
design memory systems (me, doing this). It does NOT get wired into bots.
Bots get a separate runtime protocol file in
`home/{base,linux,darwin}/claude/discord-channel/instructions/`, concatenated into
each bot's CLAUDE.md alongside `discord-bot-operating-rules.md`. The
runtime protocol is workflow-centric (see section 6).

### 6. Workflow integration (the load-bearing piece)

memory.md insists: wiring + writes are useless without an explicit
workflow telling the agent WHEN to engage memory. The runtime protocol
defines a turn as six steps:

1. **Recall (automatic)** - hook fires, ripgreps memory, prepends
   `Recall: @path1 @path2 ...` to the turn context. Agent does nothing.
2. **Triage** - agent looks at recalled paths, decides which are relevant.
3. **Read (if needed)** - agent `Read`s the recalled paths it judges
   relevant. Free to ignore irrelevant ones.
4. **Compose** - agent forms its response using recall + new input.
5. **Reply** - agent sends via the channel reply tool.
6. **Learn (deliberate)** - after replying, agent decides if anything
   durable was learned. If yes, calls `memory-write`. If no, ends turn.

The runtime protocol document spells out all six steps and the rules at
each (e.g. step 6 criteria: "save only if the fact would still be true
and relevant in 30 days").

### 7. Canonical storage path: workspace, bridged via symlink

Two candidate paths exist:

- Harness-managed: `~/.claude/projects/<cwd-encoded>/memory/`. Auto-loaded
  by the harness on session start, but opaque path, scattered across
  `~/.claude/projects/`, owned by Claude internals.
- Agent workspace: `~/.claude-discord-agents/<name>/memory/`. Visible,
  declarative, co-located with the agent's identity. But the harness does
  not auto-load `MEMORY.md` from there.

Decision: workspace path is canonical. Bridge with a symlink created at
agent workspace seeding:

    ~/.claude/projects/<cwd-encoded>/memory/  ->  ~/.claude-discord-agents/<name>/memory/

This gives both: the canonical visible path lives with the agent, AND the
harness loads `MEMORY.md` for free via the symlink. The `autoMemory-
Directory` setting cannot do this per-agent (the setting is rejected
from project/local settings for security) - symlink is the right primitive.

For non-bot agents (e.g. interactive sessions in `/Users/lucas.zanoni/.
dotfiles`): no symlink, they use the harness path directly. The recall
hook and `memory-write` CLI both compute target from cwd, so both
strategies work without code changes.

## Architecture summary

```
┌─ Discord message arrives ─────────────────────────────┐
│                                                       │
│   discord plugin presents message to agent            │
│                                                       │
│   PreToolUse hook fires (any subsequent tool call)    │
│     -> memory-recall script:                          │
│        ripgrep <memory-dir> for keywords/sender-id    │
│        emit `Recall: @path1 @path2 ...` if hits       │
│        skip if debounce window active                 │
│                                                       │
│   agent triages recalled paths                        │
│   agent Reads the relevant ones (full content)        │
│   agent composes + replies                            │
│                                                       │
│   agent decides to learn -> memory-write CLI:         │
│     validate, dedupe, append topic file,              │
│     update MEMORY.md pointer in same transaction      │
│                                                       │
└───────────────────────────────────────────────────────┘

storage:
~/.claude-discord-agents/silver/memory/         <- canonical
  MEMORY.md                                     <- one-line pointers
  user-284143065877184512.md                    <- lucas facts
  user-<other-id>.md                            <- per-discord-user
  feedback.md                                   <- corrections
  project-<name>.md                             <- per-project
  reference-<topic>.md                          <- external pointers

~/.claude/projects/-Users-...-silver/memory/    -> symlink to above
  (harness auto-loads MEMORY.md from this path,
   which resolves to the canonical workspace dir)
```

## Open questions

1. Hook debounce window: 30s? 60s? per-turn (track Claude turn boundary)?
2. memory-write LLM-check: enabled day one, or opt-in later?
3. Multi-machine sync: out of scope for v1. Per-machine memory is fine.
4. Pruning: cron-driven or run-on-write? Hook fires `memory-prune` once
   per day? Or memory-write handles it?
5. Existing harness MEMORY.md migration: if silver's harness dir already
   has files when we symlink, move them into canonical first. Not an
   issue today (dir doesn't exist), guard for future agents.
6. Recall hook trigger surface: PreToolUse fires per tool call (noisy).
   Acceptable with debounce? Or hook on UserPromptSubmit too and pick
   whichever fires for the agent's context?

## Build order

1. Write runtime protocol doc next to operating rules (workflow steps).
2. Write `memory-write` CLI (validation, dedupe, append, index update).
3. Write `memory-recall` hook script (ripgrep, score, emit, debounce).
4. Wire global hook in `~/.claude/settings.json` PreToolUse.
5. Add nix activation: create canonical dir + symlink for each discord
   agent during workspace seeding. Seed `MEMORY.md` with a header.
6. Validate end-to-end on silver: DM a fact, see memory-write fire, see
   file appear, restart bot, DM related question, observe recall.
