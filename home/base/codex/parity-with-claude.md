# Codex parity with the Claude interactive setup

A surface-by-surface comparison of how Lucas drives Claude Code interactively
versus what the Codex CLI setup provides, with the portability call for each
gap. The goal is acceptance/quality parity for a daily-driver switch, not
feature-for-feature cloning: Claude-TUI-only and clawde-agent-only mechanisms
are deliberately out of scope.

The driving asymmetry to keep in mind: interactive Claude keyboard sessions run
`claude-opus-4-8[1m]` with a 1M context window (the same `settings.json` default
that background/subagent/headless runs inherit); Codex runs `gpt-5.5` with a 272K
window. Several Claude knobs exist only because of the
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

Codex's hook subsystem is stable (`features.hooks = true`) and speaks Claude's
event vocabulary and JSON wire protocol (`PreToolUse`, `PostToolUse`,
`SessionStart`, `Stop`, ...) including `hookSpecificOutput` for model-facing
injection. Three payload facts were established by CAPTURING real Codex 0.144.1
hook input, not assumed:

- A shell command reaches the hook already Claude-shaped: `tool_name` is `Bash`
  and `tool_input.command` is a clean string (`"git add -A"`). The `/bin/zsh -lc`
  wrapper Codex uses to EXECUTE a command never reaches the hook, so the command
  guard's scanners work directly, no unwrapping needed.
- A file write reaches the hook as `tool_name` `apply_patch` with the full patch
  body (markers plus added `+` lines) in `tool_input.command`.
- `timeout` is in SECONDS (Claude uses milliseconds).

Two enforcement facts, also established live, drove the design:

- Codex honors a PreToolUse block ONLY as
  `{"hookSpecificOutput":{"permissionDecision":"deny",...}}` with exit 0. A nonzero
  exit (Claude's `continue:false` + exit-2 convention) is logged "PreToolUse
  Failed" and the tool runs anyway. So the guards emit the `permissionDecision:
  deny` schema through a shared `common/pre_tool_use_block.py`; Claude honors the
  same schema (the in-repo `monitor-streaming-pattern-validator` already relies on
  it), so one guard blocks on both CLIs.
- Codex gates hooks behind a per-invocation trust review ("hooks need review
  before they can run") that project trust does NOT satisfy and that a rebuild
  would re-invalidate (the `hooks.json` store path changes). The `codex` wrapper
  (`package.nix`) therefore launches with `--dangerously-bypass-hook-trust`, so the
  nix-managed guards run every session, matching the danger-full-access /
  approval-never posture. Without this flag the entire hooks port is inert.

Two shared helpers let one script set serve both CLIs:
`common/changed_file_paths.py` (returns `tool_input.file_path` for Claude
`Edit`/`Write`, or parses the Codex `apply_patch` `*** Add/Update/Delete File:`
markers and added-line content) and `common/codex_tool_payload.py` (a defensive
no-op on the observed `Bash`/`apply_patch` payloads; it only rewrites a
hypothetical `shell` list-command into a Claude `Bash` string). All hooks stage
flat into one store dir (`home/base/codex/hooks/hook-scripts.nix`) so sibling
imports resolve, exactly like Claude's flat `~/.claude/hooks`.

- Deployed and live-confirmed (`home/base/codex/hooks/`):
  - `SessionStart`: deep-work context load.
  - `PreToolUse` (matcher `.*`): `memory-recall.py` (shares the SAME
    `~/.claude/projects/<enc>/memory/` store as Claude, so recall continuity
    carries across both CLIs; needs `rg`), then `prohibited-command-guard.py` and
    `prohibited-words-guard.py` (the latter env-prefixed with the per-host
    `PROHIBITED_WORDS_ALLOWED` allowlist). Both block via the deny schema; the
    words guard also scans `apply_patch` bodies and file names, closing the Codex
    write-path content-scan gap (Codex writes files via `apply_patch`, not
    Write/Edit).
  - `PostToolUse` (matcher `.*`): `auto-format.py`, `record-edited-source-file.py`
    (feeds the lint ledger), `nix-rebuild-trigger.py`, all reading changed paths
    from the `apply_patch` payload.
  - `Stop` (matcher `.*`): `lint-turn-review.py` reads the ledger and surfaces a
    repo-native lint advisory for the files touched this turn.
- Live-confirmed via an isolated `CODEX_HOME` exec run: the command guard refuses
  `git add -A` ("PreToolUse Blocked") and the words guard refuses an `apply_patch`
  adding a prohibited word.
- Non-gaps confirmed: the `memory-write`/`memory-prune` CLIs are already on PATH
  for Codex (profile-global `home.packages`), and both they and `memory-recall`
  compute the same `~/.claude/projects/<enc>/memory/` dir from cwd.
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

- Claude wires: `chrome-devtools`, `vivaldi-devtools` (chise
  only), `codex` (self-referential: Claude calling Codex), `a2a` (agent-only, not
  injected into interactive sessions), and `mem0` (host-gated on a per-machine
  `mem0-host.nix`).
- Codex wires: `chrome-devtools` and `vivaldi-devtools` (chise
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
  `--sandbox danger-full-access --ask-for-approval never`. The Codex wrapper also
  passes `--dangerously-bypass-hook-trust` so its nix-managed hooks run without a
  per-session review prompt.
- Both default to maximum reasoning: Claude `effortLevel = max`, Codex
  `model_reasoning_effort = xhigh` with `model_verbosity = low` and no reasoning
  summary.
- Codex adds `fast` / `deep` / `web` profiles as its analogue of `/fast`, and a
  Claude-to-Codex plugin bridge (`claude-plugin-port`) that Claude has no
  analogue for.
- Codex's `[tui]` table is the analogue of several surfaces once believed
  Claude-only, established by probing the 0.144.4 binary and validating each key
  against a scratch `CODEX_HOME`. `tui.status_line` is a real status line, but a
  closed ordered enum of segment ids rather than Claude's arbitrary command hook:
  `git-branch`, `branch-changes`, `model-with-reasoning`, `context-used`,
  `weekly-limit`, `five-hour-limit`, `permissions`, `approval-mode`,
  `current-dir`, `thread-id` and more, colored per segment by
  `tui.status_line_use_colors`. It cannot express Claude's rate-limit reset
  countdown or threshold coloring, both of which need a command hook
  (upstream https://github.com/openai/codex/issues/17827). `tui.keymap.<context>`
  is a genuine `keybindings.json` analogue. `tui.terminal_title` drives OSC-0.
- The Done:/Next: reply shape is content, not chrome, so it ports as an
  instruction: the `codex` wrapper injects
  `agents/core_rules/communication/interactive-preferences.md` through
  `-c developer_instructions=` for interactive invocations only (no subcommand,
  a flag, `resume`, or `fork`), mirroring how `claude-workspace` appends it and
  keeping it out of `codex exec` and the MCP server, whose output is
  machine-facing. The Stop-hook gate that enforces the shape on Claude is not
  ported yet.
- Two validation facts worth keeping: the `[tui]` table is not
  `deny_unknown_fields`, so a typo'd key parses with exit 0 and an unknown
  `theme` name falls back silently, meaning "it parsed" is never evidence; and
  `CODEX_HOME=<scratch> codex debug models` is an offline config validator that
  exits non-zero with `file:line:col` serde errors on a wrong value type.
  The notice suppressors live in a top-level `[notice]` table, not `[tui.notice]`,
  which parses and is silently inert.
- Still Claude-TUI-only and out of scope: the boxed rounded composer, the
  top-right mode badge, the bullet event stream and bold section labels (all
  hardcoded ratatui, tinted only by the terminal background via OSC-11), spinner
  verbs, the OTel/usage/performance telemetry stack, the workflows JS runtime,
  and the LSP plugin packages.

## Summary of state

- Instruction body, skills bodies (and their runtime CLIs), browser MCPs,
  full-access posture, max reasoning, and context-compaction philosophy are at
  parity.
- Ported to Codex via shared, input-shape-agnostic scripts: memory recall
  (PreToolUse, shared store with Claude), the prohibited-command and
  prohibited-words guards (PreToolUse, blocking via the `permissionDecision: deny`
  schema Codex requires), auto-format + record-edited + nix-rebuild-trigger
  (PostToolUse), and lint-turn-review (Stop). The wrapper's
  `--dangerously-bypass-hook-trust` is what lets any of them run.
- Remaining ports are low value (instruction-file authoring gate, compaction
  reload nudge); everything else is a model/window limit, a documented safety
  deferral (`session-context` leak), or a Claude-TUI/launcher/clawde-agent
  artifact.
