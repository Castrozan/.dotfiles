# Codex parity with the Claude interactive setup

A surface-by-surface comparison of how Lucas drives Claude Code interactively
versus what the Codex CLI setup provides, with the portability call for each
gap. The goal is acceptance/quality parity, not feature-for-feature cloning:
Claude-TUI-only and clawde-agent-only mechanisms are deliberately out of scope.

The driving asymmetry to keep in mind: Claude (opus-4-8) has a 1M context
window; Codex (gpt-5.5) has a 272K window. Several Claude knobs exist only
because of that larger window, and have no safe analogue on the smaller one.

## Rules / instruction surface

- Claude: the full `agents/core_rules/core.md` body is deployed as
  `~/.claude/CLAUDE.md` (always-on global rules), and `~/.dotfiles/AGENTS.md`
  carries the repo-scoped instructions.
- Codex: `~/.codex/AGENTS.md` now carries the same full `core.md` body
  (`global-instructions.nix`). Codex reads `$CODEX_HOME/AGENTS.md` as
  always-on global guidance every run and merges project `AGENTS.md` walking
  from the repo root down to the cwd, so the deployed `~/.dotfiles/AGENTS.md`
  reaches Codex too. The layering matches Claude's global+project split.
- Gap: closed. The `developer_instructions` one-liner is intentionally kept as
  a concise pragmatic complement (profiles hint, repo-local-truth steer);
  duplicating the whole of `core.md` into it would only repeat the AGENTS.md
  rules in the prompt and waste window, the same reason Claude keeps
  `settings.json` lean and puts the rules in `CLAUDE.md`.

## Skills

- Claude: every `agents/skills/*` skill plus curated skill SETS (steward,
  personal) routed per session-type via `skill-injection/`, plus dynamic
  workspace skill discovery at launch via `launch-claude-workspace-session`.
- Codex: every `agents/skills/*` skill plus a generated `core` skill deployed
  flat to `~/.codex/skills/<name>/SKILL.md` (`skills.nix`). Codex has the same
  native SKILL.md slash-command-package mechanism.
- Gap: none that is portable. Codex gets the full skill set, which is the
  correct shape for interactive use. The curated session-type sets and the
  launch-time workspace discovery are clawde-agent and Claude-launcher
  specific; a flat always-available set is right for Codex.

## Slash commands

- Claude: `agents/commands/{home-assistant,phone-status}.md` deployed to
  `~/.claude/commands/`.
- Codex: supports `~/.codex/prompts/*.md`, but these two are not deployed.
- Gap: deferred. Both commands drive Lucas's personal host infrastructure
  (Home Assistant, phone over the LAN) and only work on the machine they live
  on, and both duplicate skills Codex already carries. Low acceptance/quality
  value; not worth the dead-on-other-hosts risk.

## MCP servers

- Claude wires five: `chrome-devtools`, `brave-devtools`, `codex`
  (self-referential: Claude calling Codex), `a2a`, `browser-use`.
- Codex wired only `chrome-devtools`.
- Ported now: `brave-devtools`. The `agents/skills/browser/install` module
  that `config.nix` already imports exposes the Brave command/args for free
  (same `chrome-devtools-mcp` binary pointed at the Brave profile), so this is
  a zero-new-dependency parity win that completes the browser skill's toolset
  for Codex.
- Deferred: `browser-use` (a uvx+python wrapper that would need a refactor, and
  browser automation is token-heavy against the 272K window), `a2a` (needs an
  agent-backend service Codex has no receiver for; a client without a backend
  is a false-confidence surface), `codex` (self-referential, not applicable to
  Codex itself).

## Hooks

- Claude: seven event types with many guards (memory-recall, prohibited-words,
  workspace-directory-injector, auto-format, nix-rebuild-trigger,
  session-context, end-of-turn format guard, and more).
- Codex: a single `SessionStart` hook that cats the deep-work context, with an
  undocumented stdout-injection protocol.
- Gap: deferred deliberately. Codex's hook protocol is undocumented, and the
  obvious enrichment (adding git status / recent commits to SessionStart like
  Claude's `session-context`) would pipe commit messages that reference private
  infrastructure into the model context inside a PUBLIC repo. The
  acceptance/quality upside does not justify that leakage risk. The Claude
  guards that matter most (auto-format, nix-rebuild-trigger, the reply-shape
  gate) are tied to Claude's hook JSON protocol and TUI and are not portable
  as-is.

## Context management

- Claude: 1M window on opus-4-8, auto-compact tuned to fire at 900K (90%) so a
  heavy turn keeps headroom before the wall.
- Codex: 272K window on gpt-5.5, already auto-compacting at ~95% of the window
  (model metadata default) via the `auto_compact_token_limit` mechanism.
- Gap: none that is safe. Both compact near the wall, the same philosophy.
  gpt-5.5 cannot be raised to a 1M window (a hard model limit), and lowering
  Codex's trigger below the current ~95% would compact earlier and lose more
  context, a regression. Already aligned.

## Interactive UX / how it is driven

- Both run full-access with no approval prompts: Claude via
  `dangerouslySkipPermissions` / `bypassPermissions`, Codex via
  `--sandbox danger-full-access --ask-for-approval never`.
- Both default to maximum reasoning: Claude `effortLevel = max`, Codex
  `model_reasoning_effort = xhigh` with `model_verbosity = low` and no
  reasoning summary, the speed-conscious shape.
- Codex adds `fast` / `deep` / `web` profiles as its analogue of Claude's
  `/fast` and model switching.
- Claude-TUI-only surfaces (statusline, `keybindings.json`, fish completions,
  the interactive Done:/Next: reply-shape gate) are specific to Claude Code's
  TUI and the clawde launcher and have no Codex equivalent to port.

## Summary of changes in this branch

- `~/.codex/AGENTS.md` = full `core.md` (global always-on rules).
- Model unified on `gpt-5.5` (config default, generator fallback, review_model,
  fast/deep profiles).
- `brave-devtools` MCP added to the generated Codex config.
- Three orphaned dead scripts removed.

Everything else compared above is either already at parity, a model/TUI limit,
or deferred for the documented safety reason.
