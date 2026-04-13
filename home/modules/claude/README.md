# Claude Code Module

Home-manager module for Claude Code IDE setup, configuration, skills, and persistent project agents.

## Quick Start

Enable in your home-manager configuration:

```nix
programs.claude.enable = true;
```

To add project agents (e.g., for automated project management):

```nix
claude.projectAgents.agents = {
  "my-project" = {
    projectDirectory = "/home/user/repos/my-project";
    model = "opus";
    heartbeatInterval = "3,33 * * * *";  # :03 and :33 of each hour
  };
};
```

Then rebuild: `home-manager switch`

## Module Files

### Core Configuration

| File | Purpose |
|------|---------|
| `default.nix` | Module entry point, imports all submodules |
| `claude.nix` | Base Claude Code CLI setup (binaries, data directories, environment) |
| `config.nix` | Home-manager integration and settings |
| `channels.nix` | Model channel aliases (opus, sonnet, haiku → API model IDs) |

### Agent Infrastructure

| File | Purpose |
|------|---------|
| `project-agents.nix` | Declarative project agent configuration + systemd services |
| `project-agent-instructions.md` | Shared PM identity: role, heartbeat, delegation protocol |
| `scripts.nix` | Wraps launch-project-agent script into PATH |

### Skills & Extensions

| File | Purpose |
|------|---------|
| `skills.nix` | Skill discovery and routing |
| `external-skill-sets.nix` | External skill providers (GitHub, research, etc.) |
| `personal-only-skills.nix` | Skills restricted to personal use (time-tracking, home automation) |

### System Integration

| File | Purpose |
|------|---------|
| `mcps.nix` | MCP (Model Context Protocol) server configuration |
| `plugins.nix` | Claude Code plugins |
| `hooks.nix` | Event hooks (session start, end, compaction) |
| `hook-config.nix` | Hook configuration options |
| `private.nix` | Private/sensitive configuration (credentials, tokens) |

## Directory Structure

```
home/modules/claude/
├── README.md                        # This file
├── default.nix                      # Module imports
├── claude.nix                       # Core Claude setup
├── channels.nix                     # Model channel aliases
├── config.nix                       # Settings & home-manager integration
├── skills.nix                       # Skill discovery
├── external-skill-sets.nix          # External providers
├── personal-only-skills.nix         # Personal-only skills
├── hooks.nix                        # Lifecycle hooks
├── mcps.nix                         # MCP servers
├── plugins.nix                      # Plugins
├── scripts.nix                      # Script wrappers
├── hook-config.nix                  # Hook configuration
├── private.nix                      # Private configuration
├── project-agents.nix               # Project agent systemd services
├── project-agent-instructions.md    # PM agent identity & behavior
│
├── scripts/
│   ├── launch-project-agent         # Python: creates tmux session + Claude Code
│   ├── claude-restart               # Restart Claude Code session
│   ├── claude-exit                  # Gracefully exit Claude Code
│   ├── statusline-command.sh        # Status display (e.g., for shell prompt)
│   └── bootstrap-discord-agent-heartbeat  # Discord agent bootstrap (legacy)
│
├── project-agent/
│   ├── instructions.md              # Per-project agent role (legacy location)
│   └── evals/
│       └── project_agent.yaml       # 25 evaluation tests
│
├── docs/
│   └── context-management.md        # Documentation on context layering
│
└── tests/
    ├── test_launch_project_agent.py # Unit tests for launch script
    ├── checks.nix                   # Nix derivation checks
    ├── claude-exit.bats             # Shell integration tests
    └── statusline-command.bats      # Status command tests
```

## Key Features

### 1. Persistent Project Agents

Automated project management agents that run in tmux sessions with periodic heartbeats.

**Launch ad-hoc:**
```bash
launch-project-agent ~/repo/my-project
tmux attach -t my-project
```

**Declarative (systemd):**
```nix
claude.projectAgents.agents.my-project = {
  projectDirectory = "/home/user/repos/my-project";
  model = "opus";
  heartbeatInterval = "*/15 * * * *";  # every 15 min
};
home-manager switch
systemctl --user restart claude-project-agent-my-project
```

### 2. Model Channels

Unified model aliases that map to actual API IDs:

```bash
claude --model opus       # Uses latest opus variant
claude --model sonnet     # Uses latest sonnet variant
claude --model haiku      # Uses latest haiku variant
```

Configured in `channels.nix`, editable without CLI changes.

### 3. Skills & Routing

Extensible skill system with automatic routing. Skills are organized as:
- **Top-level umbrella skills** (git, nix, session, etc.)
- **Sub-skills** organized in files within the umbrella directory

Example skill tree:
```
session/                    # Umbrella skill
  ├── claude.md            # "Launch new Claude Code sessions"
  ├── notify.md            # "Notify user at end of work"
  └── ... (other sub-skills)
```

### 4. MCP Server Integration

Connect external tools and APIs via MCP servers. Configured in `mcps.nix`:

```nix
programs.claude.mcp.servers = {
  "git-server" = { ... };
  "github-api" = { ... };
  "slack" = { ... };
};
```

### 5. Event Hooks

Lifecycle hooks that fire on Claude Code events (session start, end, compaction, etc.). Configure in `hook-config.nix`.

## Project Agent Details

A project agent is a persistent Claude Code session dedicated to managing a single project.

### What happens on first launch

1. **Validates** project has CLAUDE.md (project context)
2. **Creates** .pm/HEARTBEAT.md if missing (working memory)
3. **Reads** project CLAUDE.md to understand scope, people, repos
4. **Creates** unique persistent session ID (uuid5 from project name)
5. **Registers** heartbeat cron (via CronCreate)
6. **Asks** user 6 onboarding questions (if first session)
7. **Records** answers to HEARTBEAT.md
8. **Becomes idle** at > prompt, ready for user interaction

### Heartbeat behavior

Every 30 minutes (configurable), the agent:

1. **Wakes up** from idle (non-blocking, doesn't interrupt user)
2. **Reads** HEARTBEAT.md to check for pending work
3. **Executes** pending tasks (if any)
4. **Updates** timestamps and state
5. **Returns to idle**

If user is typing, the heartbeat waits until idle before firing.

### Agent communication style

As defined in `project-agent-instructions.md`:

- **Direct and factual** - no flowery language, state the facts
- **Delegate always** - PM agent never implements code, always delegates
- **Think in structures** - use HEARTBEAT.md, tasks, priorities
- **Cost conscious** - minimal heartbeat, lean context on resume
- **Transparent about blockers** - surface impediments immediately

### Configuration options

In `project-agents.nix`:

```nix
options.claude.projectAgents.agents = lib.mkOption {
  type = lib.types.attrsOf (lib.types.submodule {
    options = {
      projectDirectory = lib.mkOption {
        type = lib.types.str;
        description = "Absolute path to project root (must contain CLAUDE.md)";
      };
      model = lib.mkOption {
        type = lib.types.str;
        default = "opus";
        description = "Model alias: opus, sonnet, haiku";
      };
      heartbeatInterval = lib.mkOption {
        type = lib.types.str;
        default = "3,33 * * * *";
        description = "Cron expression for heartbeat interval";
      };
    };
  });
  default = { };
  description = "Declarative project manager agents";
};
```

### File layout per project

```
~/my-project/
├── CLAUDE.md              # Project context (what is this project?)
├── .pm/
│   └── HEARTBEAT.md       # Agent working memory (tasks, state)
└── sessions/
    ├── 2026-04-13.md
    ├── 2026-04-14.md
    └── ...                # Daily work logs (created by agent)
```

## Integration with dotfiles

This module follows the dotfiles conventions:

- **Nix declarative** - all configuration in home.nix
- **Systemd services** - project agents run as user systemd services
- **Path isolation** - scripts wired via Nix (no hardcoded paths)
- **Session protection** - DefaultOOMPolicy=continue prevents daemon-reload from killing tmux
- **Rebuild workflow** - changes applied via `home-manager switch` or `/rebuild`

## Testing

Run the test suite:

```bash
# From dotfiles root
tests/run.sh --quick              # Quick tests only
tests/run.sh --nix                # Full Nix evaluation
tests/run.sh                       # Complete test suite

# Specific tests
cd home/modules/claude/tests
pytest test_launch_project_agent.py -v
```

Tests cover:
- **Python** (launch-project-agent behavior)
- **Nix** (module syntax, option validation)
- **Shell** (status scripts, lifecycle commands)

## Documentation

- **architecture.md** (in .deep-work/) - System design, launch flow, context layering
- **project-agent-instructions.md** - PM agent identity and behavior
- **docs/context-management.md** - How project context is assembled
- **project-agent/evals/project_agent.yaml** - 25 evaluation tests (13 happy path + 12 adversarial)

## See Also

- [Claude Code documentation](https://claude.ai/docs/claude-code)
- [Home-manager documentation](https://nix-community.github.io/home-manager/)
- [MCP specification](https://modelcontextprotocol.io/)
