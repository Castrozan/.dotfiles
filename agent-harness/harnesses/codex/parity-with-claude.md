# Codex parity with the Claude interactive setup

A surface-by-surface comparison of how Lucas drives Claude Code interactively
versus what the Codex CLI setup provides, with the portability call for each
gap. The goal is acceptance/quality parity for a daily-driver switch, not
feature-for-feature cloning: Claude-TUI-only and clawde-agent-only mechanisms
are deliberately out of scope.

The driving asymmetry to keep in mind: interactive Claude keyboard sessions run
the model pinned in `agent-harness/harnesses/claude-code/settings/global-settings.nix` on its bare
(non-1M) variant, the same `settings.json` default that background/subagent/headless
runs inherit; Codex runs the model pinned in `agent-harness/harnesses/codex/package.nix`. The two
windows are now close in size, so the Claude knobs that once existed only for its
much larger 1M window are tuned for the bounded variant rather than being a
large-window-only concern.

## Rules / instruction surface

- Claude: the post-frontmatter body of `agent-harness/agent-instructions/core-rules/core.md` is deployed
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

- Claude: the curated interactive skill set from `agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix`
  (shared default plus claude's own additions) deploys to `~/.claude/skills/`
  alongside the generated `core` skill and the generated `all-skills` index that
  points at every non-curated skill at
  `~/.local/share/agent-skill-index/<name>/SKILL.md`, plus curated skill SETS
  routed per session-type via `skill-injection/` and the skills' bundled runtime
  CLIs installed via `skill-runtime-dependency-packages.nix`.
- Codex: the same curated interactive set (shared default plus codex's own
  additions) plus a generated `core` skill and the generated `all-skills` index
  deployed flat to `~/.codex/skills/<name>/SKILL.md` (`skills.nix`).
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
  same schema (its `pre-tool-use-dispatcher.py` emits it via
  `common/hook_dispatch.py`), so one guard blocks on both CLIs.
- Codex requires review and persisted trust for user hooks. Project trust does
  not satisfy that requirement, and rebuilt store paths invalidate the hook
  hashes. The system installs these hooks through `/etc/codex/requirements.toml`,
  which makes them managed and trusted without a per-invocation bypass.

Both CLIs now run ONE dispatcher set. Codex registers the same
`pre-tool-use-dispatcher.py`, `post-tool-use-dispatcher.py` and
`stop-dispatcher.py` Claude registers, one command per event, invoked through
the same `run-hook.sh` out of the same store path; both surfaces build that path
from `agent-harness/hooks/flat-hook-scripts-directory.nix`, which stages every
hook flat by basename so sibling imports resolve. There is no Codex-specific
script list to keep in sync, which is what the previous per-guard registration
and its hand-written 30-path allow-list cost.

Which handlers run where is declared on the handlers themselves. Every
`HookHandler` carries a `surfaces` tuple and the dispatcher filters on the
`--surface=codex` passed at registration, so one registry per event is the
auditable record of the split. Two shared helpers still absorb the payload
differences: `common/changed_file_paths.py` (returns `tool_input.file_path` for
Claude `Edit`/`Write`, or parses the Codex `apply_patch`
`*** Add/Update/Delete File:` markers and added-line content) and
`common/codex_tool_payload.py`, which canonicalizes both observed apply_patch
shapes onto the `apply_patch` tool name and maps it onto `Edit`/`Write` for
matcher purposes, so a single `Edit|Write` matcher fires on both CLIs.

- Running on the codex surface:
  - `SessionStart`: `compaction_context_recovery_handler`, registered only for
    compaction so ordinary startup, resume, and clear events stay silent.
  - `PreToolUse`: `prohibited_command_guard_handler`
    and `prohibited_words_guard_handler` (the dispatcher command is env-prefixed
    with the per-host `PROHIBITED_WORDS_ALLOWED` allowlist), plus
    `agent_instruction_file_authoring_router_handler`. The guards block via the
    deny schema; the words guard also scans `apply_patch` bodies and file names,
    closing the Codex write-path content-scan gap.
  - `PostToolUse`: `auto_format_handler`, `record_edited_source_file_handler`
    (feeds the lint ledger), `record_changed_nix_file_handler` (feeds the nix
    rebuild ledger) and `line_count_limit_guard_handler`, all reading changed
    paths from the `apply_patch` payload through `common/changed_file_paths.py`.
  - `Stop`: `lint_turn_review_handler` reads the lint ledger and surfaces a
    repo-native lint advisory for the files touched this turn, and
    `nix_rebuild_reminder_handler` reads the nix ledger and blocks once if the
    turn's nix files are still uncommitted or still unactivated.
- Live-confirmed via an isolated `CODEX_HOME` exec run: the command guard refuses
  `git add -A` ("PreToolUse Blocked"), the words guard refuses an `apply_patch`
  adding a prohibited word, and a captured `SessionStart` payload carries
  `hook_event_name` with Claude's exact key and value.
- Remaining ports: none. The last three, the instruction-authoring router, the
  line-count guard and the compaction reload nudge, all run on Codex now. The
  first two needed a real change rather than a surface flag, because both read
  `tool_input.file_path`, which an `apply_patch` payload does not carry; they go
  through `common/changed_file_paths.py` instead, which resolves the Claude
  field and the Codex patch markers alike.
- Deferred for safety: `session_context_handler` SessionStart enrichment (git status /
  recent commits) would pipe private-infra commit text into model context inside
  a PUBLIC repo. It stays `surfaces = (CLAUDE_SURFACE,)` even though Codex now
  registers the SessionStart dispatcher, and a test asserts it stays off.
- Claude-only by applicability: `codex-sandbox-downgrade-guard`,
  `monitor-streaming-pattern-validator`, and `workspace-directory-injector` are
  tied to Claude's TUI, the clawde launcher, or the `Monitor` tool.
  `background-bash-anti-pattern-validator` also runs on
  OpenCode, which has no background-bash harness but suffers the same
  foreground CI waits and interactive hangs.

## MCP servers

- Claude wires: `chrome-devtools`, `codex` (self-referential: Claude calling
  Codex), and `a2a` (agent-only, not injected into interactive sessions).
- Codex wires: `chrome-devtools`. The shared browser MCP is at parity.
- Deferred: `a2a` (needs an agent backend Codex has no receiver for) and `codex`
  (self-referential, N/A).

## Context management

- Claude: runs the bare non-1M variant; the auto-compact base and percentage are
  set explicitly in `agent-harness/harnesses/claude-code/settings/environment-variables.nix`
  (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`/`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`) so the trigger
  fires with headroom below the wall; see `agent-harness/harnesses/claude-code/docs/context-management.md`
  for the mechanism and the base-matches-window invariant.
- Codex: 272K window, auto-compacting near ~95% via `auto_compact_token_limit`.
- Gap: none that is safe. Both run bounded windows now (Claude on the non-1M
  variant), so neither side has large-window headroom to trade; lowering Codex's
  trigger would compact earlier and lose context.

## Interactive UX / how it is driven

- Both run full-access with no approval prompts: Claude via
  `dangerouslySkipPermissions` / `bypassPermissions`, Codex via
  `--sandbox danger-full-access --ask-for-approval never`. Codex loads the shared
  hooks as managed requirements, so they run without a per-session review
  prompt.
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
- Human-readable reply policy and the Done:/Next: shape are content, not chrome,
  so every interactive wrapper injects the humanize `SKILL.md` and
  its `community-language.md` and `interactive-communication.md` side files
  directly. Codex carries them through `-c developer_instructions=` for
  interactive invocations only, keeping them out of `codex exec` and the MCP
  server, whose output is machine-facing. Claude and Codex use their native Stop
  events to run the same deterministic reply guard. Harnesses without that
  return protocol call the guard from their own settled-reply adapters.
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
- Hooks are one dispatcher set serving both surfaces, registered per event and
  discriminated by a `--surface=codex` argument against each handler's `surfaces`
  tuple, so a handler ports by declaring the surface rather than by growing a
  second script. Codex blocks only via the `permissionDecision: deny` schema, and
  system-managed requirements make the Codex handlers trusted.
- No hook ports remain. What Codex still lacks is a model/window limit, a
  documented safety deferral (`session_context_handler` leak), or a
  Claude-TUI/launcher/clawde-agent artifact.
