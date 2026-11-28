### Claude project directory slug

A Claude Code transcript lives at `~/.claude/projects/<slug>/<session-id>.jsonl` where the slug replaces every
non-alphanumeric character in the absolute cwd with a dash, not just the separators. A dot in the username and a leading
dot on the directory both become dashes and produce a double dash. Reproduce it with `re.sub(r"[^a-zA-Z0-9]", "-",
path)`. Any code that reconstructs this path by replacing slashes alone will silently look in a directory that does not
exist.

### Anchor every command to an absolute path

The Bash tool's shell cwd is not reliably the primary working directory even when the harness prints that it reset it,
and it has silently drifted to an unrelated repository between two calls in one session. An unanchored push therefore
lands on whatever remote the drifted repository has. Anchor every git command with `git -C /absolute/path`, and start
nix, build and formatter invocations with an explicit absolute `cd`. Treat an unanchored push, commit or destructive
command as a defect even when it happens to work, and when a push names a remote you did not expect, inspect that
remote's refs before reverting anything.

### Claude model routing and the split budget

Claude subscription plans meter a weekly budget for Opus alone plus a separate weekly budget for every other model, on
top of a shared session limit, and all of it is shared with the web and desktop clients. Running out is therefore a
routing outcome rather than a spending one: work parked on the top tier drains one budget while the other sits
untouched.

Built-in subagents compound this, since the exploration and planning subagents inherit the session model rather than
defaulting to a cheap tier, so a fan-out on a top-tier session silently runs at that tier with nothing in the interface
saying so. A user or project subagent with the same name overrides the built-in. Never assume a built-in subagent runs
cheap, and re-read the vendor's current pricing page before quoting any figure, since all of these numbers are dated.

### Claude workflow agent calls take no turn ceiling

A workflow `agent()` call accepts only label, phase, schema, model, effort, isolation and agent type. It silently
discards anything else, so the `maxTurns` that reads like a ceiling does nothing and the call runs until the model stops
on its own. A review pass written with `maxTurns: 8` was measured at 194 assistant turns and 95 tool calls across seven
minutes, of which twelve seconds was tool execution and the rest was serial round trips. Bound such a call through its
prompt and its pinned effort, and read the run's own transcript under `subagents/workflows/wf_*` before believing any
cap.

### Claude statusline renders on conversation updates only

Claude Code's statusline command re-runs when a session's conversation state changes and never on a wall-clock timer. An
idle pane keeps its last rendered line indefinitely, so a wrong number there is almost always a frozen render rather
than a computation bug. Diagnose it by comparing a monotonically changing field across panes: if they disagree, the
panes are idle and no change to the statusline script can fix it, because the harness owns the render trigger.
Separately, GNU `stat` flags do not exist on darwin, so a statusline script that uses them is dead there.

### Claude config dir roots the whole tree

Claude Code roots its entire configuration tree at `CLAUDE_CONFIG_DIR` when set, falling back to `~/.claude`: settings,
the instruction file, skills, plugins with their marketplace and installed-plugin registries, and the top-level dotfile
all relocate together. That makes an isolated launcher the clean way to load a private marketplace or plugin without any
of it touching the default installation, while the login credential stays shared through the system keychain.

### Opencode configuration root

OpenCode uses `~/.config/opencode` under its own home directory and does not honor `CLAUDE_CONFIG_DIR`. Isolate an
OpenCode harness through its own configuration root instead of assuming Claude's override crosses harness boundaries.

### Account connectors are not in the repo

Subscription-synced account connectors are not declared anywhere in this repository and are gated by server-side feature
flags, recorded locally only as memos. There is no nix line to remove to switch them off. The one declarative off-switch
is a denied-server list in the system-level managed settings, deployed from the host module.

### Codex hooks and launch

Codex hooks mirror the Claude event vocabulary. Both configure command hook timeouts in seconds. Codex accepts a JSON
deny decision with exit zero or a blocking reason on stderr with exit two. Input rewrites require an explicit allow;
combining a rewrite with deny produces an invalid response. Writes report `apply_patch`, whose matchers also accept
`Edit` and `Write`. Follow the [native hook protocol](https://learn.chatgpt.com/docs/hooks) rather than inferring
runtime support from Claude's schema.

The on-PATH `codex` wrapper injects sandbox and approval flags and selects a generated native profile for interactive
developer instructions, leaving model selection to Codex's runtime-owned config. An explicit `--profile` selects the
caller's profile instead. Spawn it bare in a pane; re-passing a sandbox or approval flag makes it exit with a
duplicate-argument error.

Interactive launches explicitly use `--no-daemon`, keeping per-session instructions and hook environments in the owning
terminal process. Native profiles are mutable files seeded from Nix sources so model changes can persist; a symlink to
`/nix/store` makes Codex's profile writes fail. A Codex session bridged over MCP has no interactive approval channel
back to the caller, so a sandbox or approval setting weaker than full access auto-rejects escalations and strands it.

### Claude add dir skills need the nested layout

Claude Code loads skills from `--add-dir <dir>` only at `<dir>/.claude/skills/<name>/SKILL.md`; pointing it at a skill
directory itself grants file access and loads no skill, with nothing logged. On a name collision with the machine tier
at `~/.claude/skills` the session lists the name once and keeps the machine tier's description, so an added set that
overlaps the machine tier costs no extra context and can never shadow it.

### Codex skips a symlinked skill file

Codex loads a skill whose directory is a symlink, but silently skips one whose `SKILL.md` is itself a symlink, which is
exactly what home-manager produces for a recursive file entry. Nothing is logged and a directory listing shows every
entry present, so the only reliable check is to ask the agent to list the skills it can actually load. Never mark a
skill-set file entry recursive.

### Probe an environment gate past the packaged wrapper

A packaged harness binary is reached through a generated wrapper that exports every declared environment variable before
it execs, so clearing one in the calling shell and launching the harness proves nothing. The wrapper puts it back and
the probe reads as if the variable were not the gate. Probe such a gate by running the unwrapped binary, or a copy of
the wrapper with that export filtered out, and confirm the variable's absence in the running process rather than in the
shell that started it.

### Opencode ignores a prompt handed to a resumed session

Claude Code and codex both take a prompt argument beside the session they resume, and both submit it on startup. That
would spare a restart from typing into a live interface at all. opencode accepts the same shape and drops it. Neither
`--session <id> --prompt` nor `--continue --prompt` submits anything, and the session opens with an empty composer. A
restart that must cover all three harnesses therefore types the prompt into the resumed interface, and adding the prompt
to the resume command is not the simplification it looks like.

### Token analysis question and tool

Use this to find where Claude Code tokens go and to test a compaction threshold against real sessions. Run
`scripts/transcript_token_analysis/main.py` from this skill with `summary`, `tools` or `replay`, plus `--days N` and
`--current-threshold N`; the defaults are 14 days and 400000.

Run it through a read-only `explore` subagent and ask for the three outputs condensed. The transcript tree is gigabytes
on this fleet, so only the report belongs in the parent context.

### Token analysis method

Read the usage Claude Code stores on each assistant line of `~/.claude/projects/*/*.jsonl`, the approach of
[ccusage](https://npmjs.com/package/ccusage). Weight tokens by relative price: cache read 0.1, five-minute cache write
1.25, one-hour cache write 2, output 5, fresh input 1. The weights give shape, not money; the usage collector's ledger
owns priced totals.

`summary` reports cost mix, cost by session length, turn-one context as the preamble proxy, cache reads per model and
top projects. `tools` reports tool result text and image bytes per tool, and Reads of a file already read in the same
session. `replay` re-runs each session's context growth under several compaction thresholds and reports compactions and
relative cost.

### Token analysis replay validation

Validate a replay before trusting it: at the live threshold it must reproduce the observed `compact_boundary` count. On
2026-11-27 it gave 32 replayed against 33 observed.

### Transcript duplication traps

An assistant message is written once per content block, so its usage repeats; keep the last usage per message id. About
15% of `tool_result` ids repeat across lines; count each id once. Summing raw lines overcounts both.

### Token analysis measurement limits

Image tool results are base64 in the transcript, so their bytes overstate their tokens. The system prompt and built-in
tool schemas are not recorded, so turn-one context includes them while the `attachment` lines (`skill_listing`,
`instructions`, `agent_listing_delta`, `deferred_tools_delta`) size only the remainder. Models differ in price, so the
weights compare shapes within a model and do not add up across models.

### Token analysis baseline

On 2026-11-27 over 14 days, 96 sessions and 16.6k turns, cost was 71% cache read, 17% cache write and 11% output. The 10
sessions over 500 turns carried 58% of cost, and context averaged 128k tokens per turn. Turn one held a median 29k
tokens, 21% of all context tokens. Fable and Opus held 75% of cache reads. Reads of an already-read file were 129 of
800, and Read bytes were 97% image.

Replay relative cost by trigger was 100% at 400k, 74% at 200k, 68% at 150k, 64% at 100k, 68% at 75k and 119% at 50k.
Compactions per 1000 turns were 1.9, 5.0, 7.5, 14.6, 25.9 and 106.4. Cost stops improving near 100k and compaction churn
dominates by 50k.

### Token analysis decision

The trigger was set to 200k with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=20` on the 1M window, keeping the 1M window as
headroom as `agent-harness/harnesses/claude-code/docs/context-management.md` records.

### Token reduction levers

Levers by measured weight run in this order. Bound session length through the compaction trigger and task-boundary
checkpoints. Route mechanical work from Fable and Opus to cheaper models. Downscale screenshots before Read. Trim the
preamble last, since cutting 6k of 29k tokens saves about 4% in total.
