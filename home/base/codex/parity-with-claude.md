# Codex parity with the Claude interactive setup

A surface-by-surface comparison of how Lucas drives Claude Code interactively
versus what the Codex CLI setup provides, with the portability call for each
gap. The goal is acceptance/quality parity for a daily-driver switch, not
feature-for-feature cloning: Claude-TUI-only and clawde-agent-only mechanisms
are deliberately out of scope.

The driving asymmetry to keep in mind: interactive Claude keyboard sessions run
`claude-fable-5[1m]` with a 1M context window (the `settings.json` default is
`claude-opus-4-8[1m]`, which background/subagent/headless runs inherit); Codex
runs `gpt-5.5` with a 272K window. Several Claude knobs exist only because of the
larger window and have no safe analogue on the smaller one.

## Rules / instruction surface

- Claude: the post-frontmatter body of `agents/core_rules/core.md` is deployed
  verbatim as `~/.claude/CLAUDE.md` (always-on global rules), and
  `~/.dotfiles/AGENTS.md` carries the repo-scoped instructions.
- Codex: `~/.codex/AGENTS.md` carries the same `core.md` body via byte-identical
  split logic (`global-instructions.nix`). Codex reads `$CODEX_HOME/AGENTS.md` as
  always-on global guidance every run and merges project `AGENTS.md` from the
  repo root down to the cwd, so the deployed `~/.dotfiles/AGENTS.md` reaches it
  too. The layering matches Claude's global+project split.
- Gap: closed. The `developer_instructions` one-liner is intentionally kept as a
  concise pragmatic complement (profiles hint, repo-local-truth steer).

## Skills

- Claude: every `agents/skills/*` skill plus curated skill SETS routed per
  session-type via `skill-injection/`, launch-time workspace skill discovery,
  and the skills' bundled runtime CLIs installed via
  `skill-runtime-dependency-packages.nix`.
- Codex: every `agents/skills/*` skill plus a generated `core` skill deployed
  flat to `~/.codex/skills/<name>/SKILL.md` (`skills.nix`).
- No gap. The skills' runtime CLIs (`skill-runtime-dependency-packages.nix`) go
  into `home.packages`, which is the profile-global package set: the Claude and
  Codex modules are imported into the SAME home-manager config, so those CLIs are
  already on PATH for Codex. The curated session-type sets and launch-time
  workspace discovery are clawde/launcher-specific and correctly out of scope.

## Hooks

Codex's hook subsystem is now stable (`features.hooks = true`) and exposes the
same event vocabulary and JSON wire protocol as Claude: `PreToolUse`,
`PostToolUse`, `SessionStart`, `UserPromptSubmit`, `PermissionRequest`,
`SubagentStart`, `SubagentStop`, `Stop`, plus `hookSpecificOutput.additionalContext`
for model-facing injection. Input fields match Claude's (`tool_name`,
`tool_input`, `tool_response`, `cwd`, `transcript_path`). The `~/.codex/hooks.json`
schema is PascalCase-keyed like Claude's; `timeout` is in SECONDS (Claude's
registrations use milliseconds).

Two shared helpers make one script set serve both CLIs, no duplication:
`agents/hooks/common/changed_file_paths.py` (returns `tool_input.file_path` for
Claude `Edit`/`Write`, or parses Codex `apply_patch` `*** Update/Add/Delete File:`
markers) and `agents/hooks/common/codex_tool_payload.py` (rewrites a Codex `shell`
list-command `{"command":["git","add","-A"]}` into a Claude-shaped
`Bash` string so the guards' scanners work unchanged). All hooks are staged flat
into one store dir (`home/base/codex/hooks/hook-scripts.nix`) so sibling imports
resolve, exactly like Claude's flat `~/.claude/hooks`.

- Deployed now (`home/base/codex/hooks/`):
  - `SessionStart`: deep-work context load.
  - `PreToolUse` (matcher `.*`): `memory-recall.py` (shares the SAME
    `~/.claude/projects/<enc>/memory/` store as Claude, so recall continuity
    carries across both CLIs; needs `rg`), then `prohibited-command-guard.py` and
    `prohibited-words-guard.py` (the latter env-prefixed with the per-host
    `PROHIBITED_WORDS_ALLOWED` allowlist, same as Claude).
  - `PostToolUse` (matcher `.*`): `auto-format.py`, `record-edited-source-file.py`
    (feeds the lint ledger), `nix-rebuild-trigger.py`.
  - `Stop` (matcher `.*`): `lint-turn-review.py` reads the ledger and surfaces a
    repo-native lint advisory for the files touched this turn.
- Non-gaps confirmed: the `memory-write`/`memory-prune` CLIs are already on PATH
  for Codex (profile-global `home.packages`), and both they and `memory-recall`
  compute the same `~/.claude/projects/<enc>/memory/` dir from cwd.
- Guard blocking note: the guards emit `{"continue": false, ...}` and exit 2,
  which Codex parses (shared wire protocol); live hard-block under
  `danger-full-access` is expected to hold but is worth a live confirm.
- Remaining ports, lower value: `agent-instruction-file-authoring-router`
  (PreToolUse gate on the `instructions` skill) and `compaction-context-recovery`
  (SessionStart `compact` reload nudge).
- Deferred for safety: `session-context` SessionStart enrichment (git status /
  recent commits) would pipe private-infra commit text into model context inside
  a PUBLIC repo. Not ported deliberately.
- Not applicable: `codex-sandbox-downgrade-guard`, `monitor-streaming-pattern-validator`,
  `workspace-directory-injector`, `background-bash-anti-pattern-validator`, and the
  `end-of-turn-format-guard`/`tldr-reminder` reply-shape gate are tied to Claude's
  TUI, its background-bash harness, the clawde launcher, or the `Monitor` tool.

## MCP servers

- Claude wires: `chrome-devtools`, `brave-devtools`, `vivaldi-devtools` (chise
  only), `codex` (self-referential: Claude calling Codex), `a2a` (agent-only, not
  injected into interactive sessions), and `mem0` (host-gated on a per-machine
  `mem0-host.nix`).
- Codex wires: `chrome-devtools`, `brave-devtools`, and `vivaldi-devtools` (chise
  only, same host gate). The shared browser MCPs are at parity.
- Deferred: `a2a` (needs an agent backend Codex has no receiver for), `codex`
  (self-referential, N/A), and `mem0` (remote SSE memory MCP not wired on Codex;
  Lucas has explicitly deprioritized mem0).

## Context management

- Claude: 1M window; env knobs `CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` and
  `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=35` put the auto-compact trigger at ~350K
  (35%), leaving heavy-turn headroom (lowered 900K -> 500K -> 350K over time; see
  `home/base/claude/docs/context-management.md`).
- Codex: 272K window, auto-compacting near ~95% via `auto_compact_token_limit`.
- Gap: none that is safe. gpt-5.5 cannot be raised to a 1M window (hard model
  limit), and lowering Codex's trigger would compact earlier and lose context.

## Interactive UX / how it is driven

- Both run full-access with no approval prompts: Claude via
  `dangerouslySkipPermissions` / `bypassPermissions`, Codex via
  `--sandbox danger-full-access --ask-for-approval never`.
- Both default to maximum reasoning: Claude `effortLevel = max`, Codex
  `model_reasoning_effort = xhigh` with `model_verbosity = low` and no reasoning
  summary.
- Codex adds `fast` / `deep` / `web` profiles as its analogue of `/fast`, and a
  Claude-to-Codex plugin bridge (`claude-plugin-port`) that Claude has no
  analogue for.
- Claude-TUI-only surfaces (statusline, `keybindings.json`, spinner verbs, the
  Done:/Next: reply-shape gate, the OTel/usage/performance telemetry stack, the
  workflows JS runtime, the LSP plugin packages) are specific to Claude Code's
  TUI and the clawde launcher and have no Codex equivalent to port.

## Summary of state

- Instruction body, skills bodies (and their runtime CLIs), browser MCPs,
  full-access posture, max reasoning, and context-compaction philosophy are at
  parity.
- Ported to Codex via shared, input-shape-agnostic scripts: memory recall
  (PreToolUse, shared store with Claude), the prohibited-command and
  prohibited-words guards (PreToolUse), auto-format + record-edited +
  nix-rebuild-trigger (PostToolUse), and lint-turn-review (Stop).
- Remaining ports are low value (instruction-file authoring gate, compaction
  reload nudge); everything else is a model/window limit, a documented safety
  deferral (`session-context` leak), or a Claude-TUI/launcher/clawde-agent
  artifact.
