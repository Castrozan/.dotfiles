# Claude Code module

Home-manager module that installs Claude Code, declares its config, and runs persistent agents via the `clawde` framework.

## Module layout

`default.nix` imports only subdir entrypoints plus the few top-level files below.

| Path                       | Purpose                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `binary.nix`               | Pins the Claude Code binary (versioned, prefetched per-platform), exports its env vars, pre-approves the workspace trust dialog                                                                                                                                                                                                                                                                |
| `default.nix`              | Module entry point - imports the subdirs and top-level files                                                                                                                                                                                                                                                                                                                                   |
| `private.nix`              | Deploys the shared private subagents and commands from `private-config/claude/`. Private skills are not deployed here: they reach a session only through the shared catalog, so this file can never inject one behind the curated list's back                                                                                                                                                   |
| `settings/`                | `settings.json` source + keybindings + env vars + plugins, `.claude.json` trust dirs, statusline scripts, and the mutable-settings workaround                                                                                                                                                                                                                                                  |
| `agent-harness/hooks/integrations/claude/` | Deploys `agent-harness/hooks/runtime/` flat under `~/.claude/hooks/`, renders hook event registrations from the canonical event-to-dispatcher map at `agent-harness/hooks/runtime/event-to-dispatcher-map.nix`, and uses the recursive hook-tree walker. The walker deploys `.md` too, so only a runtime resource a hook reads belongs beside it; before authoring a hook, read `docs/hook-output-channels.md` for which output key reaches the model and which reaches only the human |
| `mcps/`                    | MCP server registration: interactive stdio server injection into `.claude.json` and per-agent scoped MCP config files for clawde agents                                                                                                                                                                                                                                                        |
| `skill-injection/`         | the machine-tier skill deployment (curated interactive set plus generated `core` and `all-skills` index) and the `claude-interactive` wrapper. Every harness takes its skills from one import, `agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix`, which enumerates the public and private skill roots for the building host and owns the curated list, so a skill deploys by being named there and nowhere else. A skill sits in one of four states: curated into the machine tier, indexed by `all-skills` and mirrored for reachability, named in `dotfilesRepoSkillNames` and deployed only into this repo's own project skill directories by `agent-harness/agent-instructions/repository-local-deployment/dotfiles-repo-skills-home-manager.nix`, or named in `uninjectedSkillNames` and reachable only by an agent handing its path to `skillDirectories`                                                                                                                                                                                                                                                                                                |
| `clawde-wiring.nix`        | Injects host wiring (machines registry, claude package, dotfiles path) into the external clawde flake module                                                                                                                                                                                                                                                                                   |
| `clawde-agents/`           | Shared clawde agent declarations that depend on public skill files (currently `steward`). Per-machine declarations live in `private-config/machines/<host>/clawde-*.nix`                                                                                                                                                                                                                       |
| `scripts/`                 | General Claude helper bins + their wiring (`default.nix`): claude-a2a-peer, claude-update-version, launch-command-detached, notify-turn-ended                                                                                                                                                                                                                              |
| `docs/`                    | Module documentation, not deployed to the live config: context budget and compaction (`context-management.md`), hook output channels (`hook-output-channels.md`)                                                                                                                                                                                              |

## a2a is provider-agnostic

The `a2a` command is defined in `agent-harness/agent-to-agent-communication/client/a2a-client-home-manager.nix` and runs the `a2a_cli` package in `agent-harness/agent-to-agent-communication/client/scripts/`. The provider-agnostic server package is `agent-harness/agent-to-agent-communication/server/a2a_server/`; `claude-a2a-peer` launches it for an existing herdr-attached agent.

## clawde

The persistent-agent framework lives in its own private flake at `github.com/Castrozan/clawde`, consumed as the `clawde` flake input and imported via `inputs.clawde.homeManagerModules.default`. One systemd-user service supervises one tmux session (`clawde`), with one window per agent. Each agent is declared as `clawde.agents.<name>` with an agent type (`type = "project-manager"`, defaulting to `"generic"`) that supplies role defaults inherited unless the instance overrides them, a channel adapter (`channel.type = "discord"` or `"none"`) for transport, and optional peer adapters (`expose.a2a.enable = true`).

The dotfiles owns only the host wiring (`clawde-wiring.nix` supplies `clawde.machinesRegistry`, `clawde.claudePackage`, `clawde.dotfilesRepoPath`) and the agent declarations; the module, option schema, runtime instructions, agent types, and channel adapters live in the clawde repo. Bump it with `nix flake update clawde`.

Agent declarations live per-machine in `private-config/machines/<host>/clawde-*.nix` (e.g. the per-host PM agents and rin's `clawde-silver.nix`); the shared `steward` agent, which reads the public steward skill at eval time, lives in `clawde-agents/steward.nix`.

## Testing

From the dotfiles root:

```sh
repository/verification/run.sh --quick   # bats + qml tests
repository/verification/run.sh --nix     # also runs nix evaluation checks
```

Module-specific tests live under `__tests__/`.
