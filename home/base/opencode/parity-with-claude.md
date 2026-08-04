# opencode parity with the Claude interactive setup

A surface-by-surface comparison of how Lucas drives Claude Code interactively
versus what the opencode setup provides, with the portability call for each gap.
The goal is acceptance/quality parity for a daily-driver switch, not
feature-for-feature cloning: Claude-TUI-only and clawde-agent-only mechanisms are
deliberately out of scope.

The driving asymmetry: Claude pins its model and effort in
`home/base/claude/settings/global-settings.nix`, while opencode keeps both
runtime-selectable. The config default is a starting point the model picker
(`<leader>m`, `f2`) and the variant cycler (`ctrl+t`) override per session, so
every other knob is set to its maximum-capability value rather than being traded
against the model choice.

## Provider and model

- opencode reaches models through provider credentials in
  `~/.local/share/opencode/auth.json`, not through the nix config. The `opencode`
  wrapper exports `OPENCODE_API_KEY` from the agenix secret, so the declared
  `opencode-go` default is authenticated on every host in the fleet. The free
  Zen tier was dropped; the paid Go plan is the only provider in use.
- A default naming a provider the host has not authenticated is not a validation
  error. `opencode debug config` accepts it and the failure only surfaces as an
  opaque server error on the first turn, so a model default is only proven by
  running `opencode run` against it.
- `small_model` handles title and summary generation, the analogue of Claude
  routing that work to a cheap tier.

## Rules / instruction surface

- Claude: the post-frontmatter body of `agents/core_rules/core.md` is deployed
  verbatim as `~/.claude/CLAUDE.md` (always-on global rules).
- opencode: `~/.config/opencode/AGENTS.md` carries the same body via the same
  frontmatter split (`global-instructions.nix`), and the config's `instructions`
  list loads it every run. A check asserts it stays byte-identical to the Codex
  surface, so the three CLIs cannot drift apart.
- opencode also merges project `AGENTS.md` from the repo root down to the cwd,
  so the deployed `~/.dotfiles/AGENTS.md` reaches it the way Claude's project
  `CLAUDE.md` does.
- The Done:/Next: reply shape is content, not chrome, so it ports as an
  instruction. opencode has no `--append-system-prompt` equivalent, but
  `OPENCODE_CONFIG` deep-merges a file over the global config and its
  `instructions` arrays CONCATENATE rather than replace. The `opencode` wrapper
  exploits that: it points `OPENCODE_CONFIG` at an overlay carrying
  `interactive-preferences.md` and `enforced-reply-rules.md`, and only for
  interactive invocations, mirroring how the `codex` wrapper injects
  `developer_instructions`. Every named subcommand (`run`, `serve`, `mcp`, ...)
  skips the overlay, keeping the reply shape out of machine-facing output.
- Because the wrapper owns `OPENCODE_CONFIG`, an autonomous harness that needs
  its own per-agent config file must launch `opencode.unwrappedPackage` instead,
  exactly as `codex.unwrappedPackage` exists for the same reason.

## Skills, subagents and commands

- Skills: the curated interactive set from `agents/interactive-agent-skills.nix`
  (shared default plus opencode's own additions) is deployed to
  `~/.config/opencode/skills/` along with the generated `all-skills` index that
  points at every non-curated skill at
  `~/.local/share/agent-skill-index/<name>/SKILL.md`.
  `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=true` keeps opencode from double-loading
  `~/.claude/skills/`. The skills' runtime CLIs go into `home.packages`, which is
  the profile-global package set shared with the Claude and Codex modules, so
  they are already on PATH. `opencode debug skill` lists what a given invocation
  can actually load, which is the verification command, never `ls`.
- Subagents: opencode reads agent definitions from `agent/` and `agents/` alike,
  but its frontmatter schema is not Claude's. Claude's `tools:` is a
  comma-separated allow-list string where opencode wants a permission map, and an
  invalid agent file is fatal: it fails the whole config, not just that agent. So
  `agents/subagents/*.md` is translated at build time by
  `scripts/translate_claude_subagents_to_opencode_agents.py`, which turns
  `tools:` into a deny-by-default permission map, `disallowedTools:` into an
  allow-by-default one, and drops `model:` so a subagent inherits the session's
  model rather than pinning one. Private agents from `private-config` go through
  the same translator.
- Commands: `agents/commands/*.md` deploy unchanged to
  `~/.config/opencode/command/`. opencode parses the same frontmatter and the
  same `$ARGUMENTS` placeholder, and ignores Claude's `argument-hint`.

## MCP servers

- Claude wires `chrome-devtools`, `codex` (self-referential), `a2a` (agent-only)
  and `mem0` (host-gated). Codex wires `chrome-devtools` and a work Jira server.
- opencode wires `chrome-devtools`, reusing the same stdio command the browser
  skill builds, so the shared browser MCP is at parity across all three CLIs.
- Deferred: `a2a` (needs an agent backend opencode has no receiver for), `codex`
  and a self-referential opencode server (N/A), `mem0` (explicitly
  deprioritized), and the work Jira server, whose credentials are injected from
  files by the Codex seed script; opencode's `environment` map cannot read a
  secret from a file, and this is a public repo.

## Tooling posture

- Both run full-access with no approval prompts: Claude via
  `dangerouslySkipPermissions` / `bypassPermissions`, opencode via a
  `permission` map that allows every tool. opencode's map is the better lever
  than the `--auto` flag because it can also deny, which is what the subagent
  translation depends on.
- `lsp` and `formatter` default to OFF when omitted, so both are enabled
  explicitly. Each built-in only activates when its binary is already on PATH,
  which is why enabling them is safe on a nix machine and why `nixfmt` is the
  formatter opencode picks for this repo's own files.
- `subagent_depth` defaults to 1, which forbids a subagent from launching its
  own subagents. It is raised to match Claude's nesting.
- `experimental.batch_tool` enables the batch tool, the analogue of Claude's
  parallel tool calls.
- `compaction.auto` and `compaction.prune` are the analogue of Claude's
  auto-compact window; see `home/base/claude/docs/context-management.md` for how
  the Claude side is tuned.

## TUI

- `~/.config/opencode/tui.json` is a SEPARATE file from `opencode.json`, and the
  main config silently accepts and drops `theme`, `keybinds` and `tui` keys
  rather than rejecting them. `opencode debug config` does not validate
  `tui.json` at all, so a typo there parses and is silently inert; that file is
  only proven by launching the TUI.
- `theme` follows the machine's selected theme
  (`home/base/desktop/theming/selected-theme.nix`), which is how Claude looks
  too: Claude takes its palette from the terminal, so matching the terminal is
  the parity move.
- `attention` is the analogue of Claude's
  `composer.shouldChimeAfterChatFinishes`.
- `keybinds` is a genuine `keybindings.json` analogue; `messages_undo` carries
  Claude's `ctrl+e` binding alongside opencode's own leader chord.

## Hooks

- Claude runs a dispatcher per event out of `home/base/agent-hooks/`, and Codex
  registers the same dispatchers with a `--surface=codex` flag.
- OpenCode auto-discovers JS plugins under its configuration directory.
  `opencode-hook-bridge.js` maps plugin events to the shared dispatchers with
  `--surface=opencode`. It applies pre-tool denials and input updates, carries
  post-tool formatter, lint, and rebuild guidance forward in tool output,
  rejects hard line-count violations, injects prompt context, and adds
  compaction recovery context.
- The plugin API has no synchronous end-of-turn interceptor. Claude's reply
  shape bounce therefore remains unavailable to OpenCode, where reply shape is
  enforced by instructions rather than a stop hook.

## Summary of state

- Instruction body, skills, subagents, commands, browser MCP, full-access
  posture, max reasoning default, nested subagents, language servers, formatters
  and the interactive reply shape are at parity.
- Model and effort are deliberately NOT pinned to a single choice; they are
  runtime-selectable defaults.
- OpenCode's hook bridge now covers the compatible dispatcher events. Its reply
  shape stop gate remains unavailable because the upstream plugin API does not
  expose a synchronous end-of-turn interception point, and the MCP servers
  deferred above remain credential or applicability decisions.
