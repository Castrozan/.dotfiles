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
- Gap: the skill BODIES are at parity, but Codex does NOT install the skills'
  runtime dependency packages. Several skills (todo, youtube, twitter, git
  history, exit/restart) load their SKILL.md but the CLI they tell the agent to
  run is absent from PATH on a Codex-only machine. Portable and valuable;
  highest-ROI non-hook follow-up. The curated session-type sets and launch-time
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

- Deployed now (`home/base/codex/hooks/`): `SessionStart` deep-work context load
  plus two `PostToolUse` hooks running the SHARED `agents/hooks/post-tool-use`
  scripts, `auto-format.py` and `nix-rebuild-trigger.py`. The scripts are
  input-shape-agnostic: `agents/hooks/common/changed_file_paths.py` returns
  `tool_input.file_path` for Claude's `Edit`/`Write`, or parses Codex
  `apply_patch` `*** Update/Add/Delete File:` markers out of the tool payload.
  One script set, both CLIs, no duplication.
- The one wrinkle handled: Codex edits arrive as `apply_patch` patches under the
  `shell`/`apply_patch` tool, so the changed path is not in `tool_input.file_path`
  the way Claude exposes it. The shared parser extracts it from the patch text.
- Remaining Claude hooks, ranked by daily-driver value, as the follow-up port
  list (all now technically portable onto Codex's `features.hooks`):
  - `memory-recall` (PreToolUse) + `memory-write`/`memory-prune` CLIs + the
    `MEMORY.md` file store: the single biggest continuity capability; recall
    injection depends on the PreToolUse protocol and the Claude memory dir, so it
    needs a Codex-specific adapter.
  - `record-edited-source-file` + `lint-turn-review` (PostToolUse + Stop):
    end-of-turn repo-native lint of the files touched this turn.
  - `prohibited-words-guard` (PreToolUse): public-repo leak guard on
    commit/tag/MR-create commands. Top SAFETY follow-up.
  - `prohibited-command-guard` (PreToolUse): blocks `git add -A`/`.` and other
    footguns.
  - `agent-instruction-file-authoring-router` (PreToolUse): gates edits to
    instruction surfaces on the `instructions` skill being loaded.
  - `compaction-context-recovery` (SessionStart `compact`): reload-trackers nudge.
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

- Instruction body, skills bodies, browser MCPs, full-access posture, max
  reasoning, and context-compaction philosophy are at parity.
- `PostToolUse` auto-format and nix-rebuild-trigger hooks are PORTED to Codex via
  shared input-shape-agnostic scripts.
- Highest-value remaining ports: the memory system, the skills' runtime CLIs,
  end-of-turn lint review, and the two publish/command safety guards.
- Everything else is a model/window limit, a documented safety deferral, or a
  Claude-TUI/launcher/clawde-agent artifact.
