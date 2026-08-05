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
`agent-harness/agent-instructions/skills/` and cannot see a foreign tree, so any repository can inject any amount into the system prompt just by
being the directory you opened.

**The knowledge tier does not travel.** `agent-memory.md` says no registry edit is needed to add a domain because "the
interactive workspace launcher materializes every one of them into the session's skill namespace". True only inside
`~/.dotfiles`. Outside it, `nix`, `coding`, `clawde`, `agent-harness`, `desktop` and `arr-stack` and their `knowledge.md`
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

## The design: curated tiers, all native

**Machine tier, `~/.claude/skills/`.** Each interactive harness receives a curated set from
`interactive-agent-skills.nix`, plus a generated `all-skills` index for the source skills outside that set. This bounds
always-on descriptions while retaining a path to domain knowledge. Machine-private skills are enumerated by that same
catalog under the building host's name, so they obey the same curation and reach a session that does not curate them
only through the index.

**Repository tier, `<repo>/.claude/skills/`.** Owned and curated by the repository, discovered natively by walking up
from the working directory. A repo with none gets none. `ai-first-initiative` already has this and the launcher was
hiding it. `~/.dotfiles` needed no such directory while all of its skills belonged to the machine tier; the follow-up
below is where that stopped holding.

**Agent tier, `~/.local/share/claude-skill-sets/<set>/.claude/skills/`.** Nix declares this per agent and passes it
through the agent's launch command. Curation here remains necessary because autonomous agents can have harness-specific
skill roots.

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

Discovery remains native for repository and agent scopes. The curated machine tier avoids loading every source skill by
default, while the generated index keeps each excluded skill and its durable knowledge reachable.

## Explicitly rejected

Packaging `agent-harness/agent-instructions/skills/` as a plugin with a local marketplace. It would allow per-project enable and disable through
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

`skill-set-builders.nix` discovers the source skill set, and `interactive-agent-skills.nix` owns the shared curated list
that each harness deploys. A private skill still cannot leak into another machine's namespace, because the private roots
are read under the building host's name.

The `personal` set and the `skillDirectories` entries that pointed at it are gone from jenny, golden and claude, since
all three now receive the same skills from the machine tier. The named skill sets survive for the codex agents, which
never read `~/.claude/skills`.

`launch-claude-workspace-session`, its nine tests, their `conftest.py` and a dead bash predecessor at
`scripts/claude-workspace` are deleted, 1655 lines in total. `claude-interactive` replaces them: it exports the marker
and appends the interactive surfaces with `--append-system-prompt-file`, verified end to end against 2.1.220. It passes
no `--model`, because `settings.json` already pins the same value, and no effort flag, because `binary.nix` already
exports `CLAUDE_CODE_EFFORT_LEVEL`.

The curated machine tier balances reachability with context cost. A harness receives the shared set, its own additions,
and the generated `all-skills` index for everything else, rather than every source skill by default.

One behavior stays untested: which side wins when a repository tier skill and a machine tier skill share a name. Either
direction is acceptable, because both sets are curated and reviewed, unlike the 301 drops the walk performed, but the
answer belongs in `agent-harness/knowledge.md` once someone hits it.

## Follow-up: the curated machine tier and the all-skills index

The machine tier stopped carrying every skill. `agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix` now owns a shared curated list,
`defaultInteractiveSkillNames`, and each harness module passes its own additions and removals through
`effectiveInteractiveSkillNames`, so claude, codex and opencode each deploy only their effective set into their own
skills directory. The `claude-machine-tier-carries-every-skill` check was replaced by three invariants: the curated set
must all deploy, the generated `all-skills` index must deploy, and every skill excluded from the curated set must stay
reachable at `~/.local/share/agent-skill-index/<name>`, deployed by `home/base/agents/interactive-skill-index.nix`.

The former `personal` umbrella skill was deleted and replaced by a nix-generated `all-skills` skill, built like `core`
from `renderAllSkillsIndexSkill` in `interactive-agent-skills.nix`. Its frontmatter description names every skill not
curated-injected for that harness, and its body points at each indexed skill's reachable path. Its chapters became real
skills: `agent-harness/agent-instructions/skills/obsidian` and `agent-harness/agent-instructions/skills/passwords`.

## Follow-up: the third state, skills no interactive session reaches

Curated and indexed were the only two states, so every skill on disk cost every session at least an index line. A skill
that exists for one autonomous agent, or for one machine's hardware, earned none of that. `uninjectedSkillNames` in
`interactive-agent-skills.nix` is the third state: named there, a skill deploys into no machine tier, appears in no
`all-skills` index and gets no mirror under `~/.local/share/agent-skill-index`, so the only way to reach it is an agent
naming its path through `skillDirectories`. `claude-uninjected-skills-reach-no-global-surface` asserts all three
absences together, because any one of them alone would put the skill back in every session's budget.

A skill only one machine can act on belongs in that machine's private root rather than in the shared uninjected list:
the catalog reads `private-config/machines/<hostname>/skills` under the building host's name, so it is absent from every
other machine by construction instead of by a name someone has to keep listing.

The knowledge tier still travels, with a change in reachability: a fact filed under an indexed skill's `knowledge.md`
is not in the machine tier, but the index points at it and the mirror keeps the whole skill directory reachable, so the
promise of `agent-memory.md` holds through one index read. The 9471-byte always-on description figure is now the
curated set's cost; the index description is the price of every other domain being reachable, and the per-harness
description budgets are bounded by the curated list plus one line.

## Follow-up: the fourth state, skills scoped to the repository they describe

`nix` and `agent-harness` describe the dotfiles tree and nothing else, yet the machine tier charged every session for
their descriptions, including sessions in unrelated repositories. `dotfilesRepoSkillNames` in
`interactive-agent-skills.nix` is the fourth state: named there, a skill leaves the machine tier, the `all-skills` index
and the reachability mirror exactly as an uninjected one does, but instead of waiting for an agent to name its path it
deploys into the dotfiles checkout's own project skill directories, which every harness discovers by walking up from the
working directory. `home/base/agents/dotfiles-repo-skills.nix` writes them, gitignored, the same way
`dotfiles-repo-agent-instructions.nix` writes `AGENTS.md` and `CLAUDE.md` into the same checkout.

The tier is deliberately plural, because the project convention is per harness rather than shared: Claude reads
`.claude/skills`, OpenCode reads `.opencode/skills`, and one list of conventions in the shared module covers both from a
single source, so adding a harness is one entry rather than a new module. Codex is the exception that shapes the rest of
the design: it discovers skills only under `$CODEX_HOME`, so no project directory reaches it, and `agent-harness/agent-instructions/project-context/dotfiles-agent-instructions.md`
names the in-tree paths instead. That instruction file is itself the harness-agnostic floor here, since every harness
loads it when working in the repository.
