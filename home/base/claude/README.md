# Claude Code module

Home-manager module that installs Claude Code, declares its config, and runs persistent agents via the `clawde` framework.

## Module layout

`default.nix` imports only subdir entrypoints plus the few top-level files below.

| Path | Purpose |
|------|---------|
| `binary.nix` | Pins the Claude Code binary (versioned, prefetched per-platform), exports its env vars, pre-approves the workspace trust dialog |
| `default.nix` | Module entry point - imports the subdirs and top-level files |
| `private.nix` | Deploys private agents/skills from `private-config/` (per-machine and shared) |
| `personal-only-skills.nix` | List of skills restricted to personal (non-work) sessions |
| `settings/` | `settings.json` source + keybindings + env vars + plugins, `.claude.json` trust dirs, statusline scripts, and the mutable-settings workaround |
| `hooks/` | Deploys `agents/hooks/` flat under `~/.claude/hooks/` (`default.nix`), hook event registrations (`event-registrations.nix`), and the recursive hook-tree walker |
| `mcps/` | MCP server registration: supergateway bridge runners, injection into `.claude.json`, browser-use config patcher |
| `skill-injection/` | `claude` fish wrapper, the `claude-workspace` launcher (`scripts/`), and the skill-set builders |
| `clawde/` | Persistent agent framework: tmux session + supervisor + channel/peer adapters |
| `clawde-agents/` | Shared clawde agent declarations that depend on public skill files (currently `steward`). Per-machine declarations live in `private-config/machines/<host>/clawde-*.nix` |
| `scripts/` | General Claude helper bins + their wiring (`default.nix`): memory-write/prune, claude-a2a-peer, claude-update-version, launch-command-detached, notify-turn-ended |
| `completions/` | `claude.fish` completion (installed by `home/base/terminal/fish.nix`) |
| `docs/` | Module documentation |

## a2a is provider-agnostic

The a2a MCP client (the `a2a-mcp-server` npm package that lets an agent call peers) lives in the shared `home/base/agents/a2a/` layer, not inside this module:

| Path | Purpose |
|------|---------|
| `home/base/agents/a2a/install.nix` | Single source for the npm install + binary/command/args, consumed by any provider |
| `home/base/agents/a2a/default.nix` | Runs the install activation exactly once |
| `home/base/agents/a2a/register.nix` | `registerStdioServerInJsonConfig` helper for providers that register a2a via stdio |

Claude registers a2a as an HTTP bridge in `mcps/` (consuming `a2a/install.nix`); codex/opencode/hermes can register it via the same shared layer. The real A2A server implementation is the provider-agnostic Python package at the repo-root `agents/a2a_server/`.

## clawde

`clawde/` is the persistent-agent framework. One systemd-user service supervises one tmux session (`clawde`), with one window per agent. Each agent is declared as `clawde.agents.<name>` with a channel adapter (`channel.type = "pm"` or `"discord"`) and optional peer adapters (`expose.a2a.enable = true`).

See `clawde/default.nix` for the option schema, `clawde/instructions/clawde-runtime.md` for runtime rules, and `clawde/channel-adapters/<name>/instructions/<name>-runtime.md` for per-channel behavior.

Agent declarations live per-machine in `private-config/machines/<host>/clawde-*.nix` (e.g. the per-host PM agents and rin's `clawde-silver.nix`); the shared `steward` agent, which reads the public steward skill at eval time, lives in `clawde-agents/steward.nix`.

## Testing

From the dotfiles root:

```sh
tests/run.sh --quick   # bats + qml tests
tests/run.sh --nix     # also runs nix evaluation checks
```

Module-specific tests live under `tests/`.
