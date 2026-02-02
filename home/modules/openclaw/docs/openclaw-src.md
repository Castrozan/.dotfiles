# OpenClaw Source Reference

Source: `~/repo/openclaw` (checked out at installed version tag)
Version synced from: `home/modules/openclaw/install.nix`

## Project Structure

TypeScript/Node.js monorepo — personal AI assistant gateway routing messages between platforms and agents.

### Core (`src/`)
- `gateway/` — WebSocket control plane server
- `routing/` — message routing (channel → agent → session)
- `agents/` — AI agent runtime, Pi integration, model selection
- `sessions/` — session management (main, peer, subagent, isolated)
- `channels/` — channel abstractions, allowlists, typing indicators
- `plugins/` — plugin system for extensions
- `cron/` — cron job scheduler
- `infra/` — heartbeat, events, system state
- `config/` — configuration types and loading

### Built-in Channels
Telegram (grammY), Discord (discord.js), Slack (Bolt), WhatsApp (Baileys), Signal (CLI), iMessage (macOS), WebChat

### Extension Channels (`extensions/`)
BlueBubbles, Matrix, MS Teams, Google Chat, Line, Zalo, Nextcloud Talk, Nostr, Twitch

### Extension Services (`extensions/`)
- Memory: LanceDB, memory-core
- Services: diagnostics-otel, voice-call, llm-task, lobster
- Auth helpers: google-gemini-cli-auth, google-antigravity-auth, minimax-portal-auth

### Native Apps (`apps/`)
macOS (Swift menu bar), iOS, Android — camera, voice, canvas

### Bundled Skills (`skills/`)
50+ skills: 1password, github, notion, obsidian, canvas, browser, coding-agent, openai-whisper, gemini, clawhub, discord, himalaya (email), local-places, model-usage, etc.

## Message Flow

```
Platform → Channel Adapter (allowlist) → Routing (resolve agent+session) → Agent Runtime (Pi) → Tools Execution → Response → Platform Delivery
```

## Configuration (`~/.openclaw/openclaw.json`)

Key sections:
- `agents.list[]` — agent definitions (id, name, model, workspace, tools, sandbox)
- `agents.defaults` — default agent settings
- `bindings[]` — map channels/peers/groups/accounts to agent IDs
- `channels.*` — per-platform config (tokens, groups, allowlists)
- `cron.jobs[]` — scheduled jobs (system_event, heartbeat, isolated_agent)
- `tools.*` — tool policies (allow/deny lists, groups)
- `skills.entries` — per-skill config and env overrides
- `plugins.*` — plugin allowlist and config
- `models.providers` — model provider auth and fallbacks
- `session.dmScope` — session isolation level (main, per-peer, per-channel-peer)
- `gateway.*` — bind address, port, tailscale, auth

## Routing

Resolution order for bindings: peer → guild → team → account → channel → default

Session key format: `agent:{agentId}:{mainKey}` or `agent:{agentId}:{channel}:{accountId}:{peerId}`

`dmScope` controls isolation: `main` (collapsed), `per-peer`, `per-channel-peer`, `per-account-channel-peer`

## Agent System

### Config per agent
```
id, name, workspace, model (primary + fallbacks),
memorySearch, heartbeat, identity (name, avatar),
groupChat (activation, requireMention),
subagents (allowAgents, model),
sandbox (mode, scope, workspaceAccess, docker, browser),
tools (allow, deny, groups)
```

### Context Injection
Template files injected into system prompt: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, BOOTSTRAP.md, BOOT.md

Located in workspace dir or `docs/reference/templates/` (defaults).

### Model Selection
Primary model + fallback chain. Auth profiles with OAuth/API keys. Profile rotation on quota/rate limits. Credentials at `~/.openclaw/credentials/`.

## Session Types

| Type | Key pattern | Use |
|------|------------|-----|
| Main | `agent:{id}:main` | Direct 1:1 chat |
| Peer | `agent:{id}:{channel}:{account}:{peer}` | DM/group conversations |
| Subagent | includes `subagent:` | Spawned workers |
| Isolated | `cron:{jobId}` | Cron agent turns |
| Thread | includes `:thread:{id}` | Slack threads, Telegram topics |
| ACP | includes `acp:` | External clients (Control UI, mobile) |

Session storage: `~/.openclaw/agents/{agentId}/sessions/{sessionKey}.jsonl`

## Cron System

Job types:
- **system_event** — enqueue text to agent main session
- **heartbeat** — run health check across channels
- **isolated_agent** — spawn isolated session with message

Config: `cron.jobs[]` with schedule (cron expression), type, agentId, message, timeout.
State: `~/.openclaw/cron.json`, logs at `~/.openclaw/cron/logs/{jobId}.jsonl`.

## Plugin System

Plugin manifest provides: tools, hooks, channels, providers, commands, HTTP handlers, CLI registrars, config schemas.

Discovery from `extensions/*/package.json`, loaded via jiti dynamic import.

## Skill System

Skill entry: `SKILL.md` + optional metadata (os, requires.bins, requires.env, requires.config).

Sources: bundled `skills/`, workspace `skills/`, plugin-provided, ClawHub registry.

## Extension Points

- **New channel**: extension in `extensions/`, implement `ChannelPlugin`, export via manifest
- **New tool**: definition in `src/agents/tools/`, register in coding tools or plugin
- **New skill**: `skills/{name}/SKILL.md` with frontmatter metadata, auto-discovered
- **New plugin**: `extensions/{name}/` with `openclaw.manifest.ts`
- **New agent**: add to `agents.list[]`, bind to channels, optional custom workspace templates
