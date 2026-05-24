# Claude Code module

Home-manager module that installs Claude Code, declares its config, and runs persistent agents via the `clawde` framework.

## Module layout

| Path | Purpose |
|------|---------|
| `claude.nix` | Pins the Claude Code binary (versioned, prefetched per-platform) |
| `claude-environment-variables.nix` | Env vars Claude reads at startup |
| `config.nix` | settings.json source + activation that keeps it mutable |
| `default.nix` | Module entry point - imports all the .nix files in this dir |
| `clawde/` | Persistent agent framework: tmux session + supervisor + channel/peer adapters |
| `external-skill-sets.nix` | `claude` fish wrapper + claude-workspace launcher with personal skill set |
| `hook-config.nix` | Hook event registrations (PreToolUse, PostToolUse, Stop, etc.) |
| `hooks.nix` | Walks agents/hooks/ recursively, deploys each script flat under ~/.claude/hooks/ |
| `list-hook-scripts-recursively.nix` | Helper that walks the hooks tree |
| `mcps.nix` | MCP server registrations |
| `plugins.nix` | Claude Code plugins |
| `private.nix` | Private config that should not be committed (gitignored) |
| `scripts.nix` | Wires extra bins into PATH: memory-write, memory-prune, claude-update-version, claude-a2a-peer |
| `skills.nix` | Deploys agents/skills/ to ~/.claude/skills/ (base) and the personal vault |
| `workspace-trust.nix` | Marks ~/repo/* + ~ + ~/.dotfiles as trusted in .claude.json |
| `workarounds/` | Compensations for upstream issues (install-method, mutable settings) |

## clawde

`clawde/` is the persistent-agent framework. One systemd-user service supervises one tmux session (`claude-discord`), with one window per agent. Each agent is declared as `clawde.agents.<name>` with a channel adapter (`channel.type = "pm"` or `"discord"`) and optional peer adapters (`expose.a2a.enable = true`).

See `clawde/default.nix` for the option schema, `clawde/instructions/clawde-runtime.md` for runtime rules, and `clawde/channel-adapters/<name>/instructions/<name>-runtime.md` for per-channel behavior.

Agents are configured at the user level in `users/<user>/home/clawde-agents.nix`.

## Testing

From the dotfiles root:

```sh
tests/run.sh --quick   # bats + qml tests
tests/run.sh --nix     # also runs nix evaluation checks
```

Module-specific tests live under `tests/`.
