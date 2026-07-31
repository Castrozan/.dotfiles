# Session Context Loading

`agent-memory.md` closed on a claim it never verified: that filing a fact under its owning skill is enough, because
"that owner's existing loading semantics do the tiering for free". Measured, those semantics hold in exactly one
directory. Six of the eight `knowledge.md` files that design produced are unreachable from anywhere except
`~/.dotfiles`, because skill discovery for an interactive session is not the harness's. It is a 484-line launcher that
walks the working directory, aggregates every `SKILL.md` under it into a `/tmp` namespace, and hands that namespace over
with `--add-dir`.

That walk reproduces on the skill axis the failure the memory work removed on the fact axis: an unbudgeted, unreviewed,
silently lossy always-on surface, derived from where files happen to sit rather than from a decision anyone made.

## What breaks

Measured on kira, 2026-07-31, claude-code 2.1.220, by running the launcher's own discovery function over each root:

| Root opened | Walk | `SKILL.md` found | Unique after dedupe | Silently dropped | Eager description bytes |
|---|---|---|---|---|---|
| `~/.dotfiles` | 0.04s | 46 | 46 | 0 | 10378 |
| `~/repo/ai-first-initiative` | 0.03s | 48 | 32 | **16** | 6658 |
| `~/repo` | 0.69s | 418 | 117 | **301** | **24046** |
| `~/code` | 0.04s | 0 | 0 | 0 | 0 |

Opening `~/repo` puts 24046 bytes of skill descriptions into the system prompt. That is 26 percent more than the
19008-byte memory index this repo deleted for being an unreviewed always-on surface, and it arrives having already
discarded 301 of the 418 skills it found.

Deduplication is by directory name. The shallowest lexicographically first path wins and the rest vanish with no report.
In `ai-first-initiative` that resolves `jira` to `betha-desenvolvimento/packages/jira` and drops the `betha-triagem` one
on sort order alone. In `~/repo` the colliding pairs include `aplicacoes-atendimento-triage` against
`betha-ai-maintainer`, the same two subjects the original context-bleed report named.

Five of the 46 in `~/.dotfiles` are not skills for this session at all. `home/base/sourcebot/skill` is a deployment
template that happens to contain a `SKILL.md`, and four are `private-config/machines/rin/skills/*`, another machine's
private skills loaded on this one.

## The defects

**Discovery is keyed on the working directory.** This is the same category error the memory stores made, and it fails
the same way: a subject is not a directory. The skills a session needs follow the human and the machine, not the tree
they happened to `cd` into.

**The walk is lossy and silent.** A name collision resolves by path sort order and reports nothing. Nobody chose which
`jira` wins, and nobody can tell that a choice was made.

**It prunes the one directory the harness uses.** `discover_workspace_skill_source_directories` skips every child whose
name starts with a dot, so `<repo>/.claude/skills/` is the single tree it never reads. `ai-first-initiative` curates
nine skills there; the walk ignores those nine and injects 32 accidental ones instead.

**Nothing bounds it.** The repo caps its own always-on instruction and description budgets in a test. That test governs
`agents/skills/` and cannot see a foreign tree, so any repository can inject any amount into the system prompt just by
being the directory you opened.

**The knowledge tier does not travel.** `agent-memory.md` says no registry edit is needed to add a domain because "the
interactive workspace launcher materializes every one of them into the session's skill namespace". True only inside
`~/.dotfiles`. Outside it, `nix`, `git`, `clawde`, `claude-harness`, `desktop` and `arr-stack` and their `knowledge.md`
files do not exist, which is precisely the tier the memory design depends on.

## What the harness already does

Verified on 2.1.220 rather than assumed:

Personal skills at `~/.claude/skills/` load in every session on the machine. Project skills at `<root>/.claude/skills/`
load natively, found by walking **up** from the working directory: a probe skill was named from three levels below the
root that declared it. Extra sets load from `--add-dir <dir>` when `<dir>` contains `.claude/skills/`, which is the
mechanism jenny already uses in production. Skill descriptions are eager: the probe named a skill it had never invoked.

Model and effort are already set globally and the launcher's copies are dead weight. `model = "claude-opus-5[1m]"` is in
the deployed `settings.json` and `CLAUDE_CODE_EFFORT_LEVEL = "max"` is exported by the `claude` wrapper in
`binary.nix` for every session. `--append-system-prompt-file` exists alongside `--append-system-prompt`, so the
launcher reading the file into an argv string is also unnecessary.

The fleet already composes a session natively. jenny launches as `claude --model sonnet --name jenny --permission-mode
bypassPermissions --append-system-prompt "$(cat instructions/jenny.md)" --add-dir <skill set>` inside a workspace that
carries its own `.claude/settings.json`. Nothing bespoke, and it is the only Claude agent on the fleet; the other three
run codex and take skills through their own path.

## The design: three tiers, all native

**Machine tier, `~/.claude/skills/`.** Every skill in `agents/skills/`, nix-declared, loaded in every session on the
machine regardless of directory. This is the tier that carries `knowledge.md`, so filing a fact under its owner finally
means what `agent-memory.md` said it meant. Cost is 9471 bytes of descriptions, already the number the existing budget
test caps at 12000, which stops being notional and becomes the real always-on figure. Machine-private skills such as
`private-config/machines/rin/skills/*` deploy into this tier from the module that already knows the host, so rin's
skills stay on rin.

**Repository tier, `<repo>/.claude/skills/`.** Owned and curated by the repository, discovered natively by walking up
from the working directory. A repo with none gets none. `ai-first-initiative` already has this and the launcher was
hiding it. `~/.dotfiles` needs no such directory, since all of its skills belong to the machine tier.

**Agent tier, `~/.local/share/claude-skill-sets/<set>/.claude/skills/`.** Unchanged. Nix-declared per agent, handed over
with `--add-dir` from the agent's launch command. Curation here is real because the codex agents that consume it never
read `~/.claude/skills/`.

The `personal` set falls out. Its only consumer is jenny, who already receives all 41 skills as ten globals plus
thirty-one from that set, and who would receive the same 41 from the machine tier.

## What has no native equivalent

Exactly one thing survives: the interactive-only system prompt of `interactive-preferences.md`, `enforced-reply-rules.md`
and `adaptive-implementation-delivery-process.md`. `~/.claude/CLAUDE.md` would reach jenny too. There is no settings key
for it. A `SessionStart` hook injects context that compaction may drop, and these are rules that must hold as the
conversation grows long, so the context tier is the wrong tier. A launch flag is required, which means a wrapper
survives at two lines: export the marker, exec `claude --append-system-prompt-file <store path> "$@"`.

The marker must ship with the rules. Inverting detection to "interactive unless `CLAWDE_AGENT_NAME` is set" is wrong: a
bare `claude` would then be format-guarded by the Stop hook without ever having received the format rules it is judged
against. The existing `CLAWDE_AGENT_NAME` check in `interactive_session_detection.py` stays as the second gate, which
also makes the launcher's environment scrub redundant.

## Consequences

| Root opened | Eager description bytes before | After | Skills silently dropped before | After |
|---|---|---|---|---|
| `~/.dotfiles` | 10378 | 9471 | 0 | 0 |
| `~/repo/ai-first-initiative` | 6658 plus its own nine | 9471 plus its own nine | 16 | 0 |
| `~/repo` | 24046 | 9471 | 301 | 0 |
| `~/code/lucaszanoni-web` | 2458 | 9471 | 0 | 0 |

The worst case improves by 2.5x and stops losing skills. The clean case pays 7013 more bytes, about 1750 tokens, and
that is the price of every domain's knowledge being reachable from every directory, which is the whole point.

Discovery becomes strictly more capable, not less. The launcher descends from the working directory, so opening a
subdirectory of a repository finds only what is below it. Native discovery ascends to the project root, so the repo's
skills load from anywhere inside it.

1314 lines are deleted: 484 in the launcher and 830 across its nine test files. Gone with them are the sha256 `/tmp`
namespace, the staging swap, both stale sweeps, the `--from` flag and the environment scrub.

## Explicitly rejected

Packaging `agents/skills/` as a plugin with a local marketplace. It would allow per-project enable and disable through
`enabledPlugins`, and the repo already has a private marketplace pipeline, but it adds a manifest, a marketplace entry
and an install step to solve a scoping problem that three tiers already solve for one human on their own machines.

Keeping the cwd walk and making it safe by bounding the count and reporting collisions. That buys a correct version of
the wrong shape. The set of skills a session should have is a decision, and deriving it from a filesystem scan means
nobody ever makes that decision.

Per-agent `CLAUDE_CONFIG_DIR` to hide the machine tier from agents. It relocates settings, the instruction file, plugins
and their registries together, so isolating skills would mean rebuilding an entire config tree per agent.

Injecting the interactive rules through `SessionStart`. Compaction can drop injected context, and a reply-shape rule
that survives only until the first compaction is worse than none.

## What shipped

`skill-set-builders.nix` no longer splits skills into a global list and a specialized remainder; there is one list,
`allSkillNames`, and `all-sessions-global.nix` deploys all of it into the machine tier. Machine-private skills already
took this path: `private.nix` deploys `private-config/machines/<host>/skills/*` into `.claude/skills` for that host
only, so removing the walk is what stops rin's four private skills from loading on kira.

The `personal` set and the `skillDirectories` entries that pointed at it are gone from jenny, golden and claude, since
all three now receive the same skills from the machine tier. `claudeCuratedSkillSets` survives for the codex agents,
which never read `~/.claude/skills`.

`launch-claude-workspace-session`, its nine tests, their `conftest.py` and a dead bash predecessor at
`scripts/claude-workspace` are deleted, 1655 lines in total. `claude-interactive` replaces them: it exports the marker
and appends the interactive surfaces with `--append-system-prompt-file`, verified end to end against 2.1.220. It passes
no `--model`, because `settings.json` already pins the same value, and no effort flag, because `binary.nix` already
exports `CLAUDE_CODE_EFFORT_LEVEL`.

Two agents pay for the machine tier. `monster` on chise and `silver` on rin declare `skillDirectories = [ ]` and today
see only ten skills, so they gain about 1750 tokens of descriptions per session. That is the accepted price of one list
with no curation to drift. If it ever bites, `CLAUDE_CONFIG_DIR` is the escape hatch, at the cost of rebuilding a
config tree for that agent.

One behavior stays untested: which side wins when a repository tier skill and a machine tier skill share a name. Either
direction is acceptable, because both sets are curated and reviewed, unlike the 301 drops the walk performed, but the
answer belongs in `claude-harness/knowledge.md` once someone hits it.
