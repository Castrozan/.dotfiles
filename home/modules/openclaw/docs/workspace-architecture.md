# OpenClaw Workspace Architecture — Compiled Findings

## How OpenClaw Loads Workspace Files

### Bootstrap File Injection

OpenClaw hardcodes exactly 8 bootstrap files that get auto-injected into agent context at session start:

1. `AGENTS.md` — operating instructions
2. `SOUL.md` — persona, tone, boundaries
3. `TOOLS.md` — local environment notes (agent-writable)
4. `IDENTITY.md` — agent name, emoji, vibe
5. `USER.md` — human profile
6. `HEARTBEAT.md` — heartbeat checklist (agent-writable)
7. `BOOTSTRAP.md` — first-run only (then deleted)
8. `MEMORY.md` — long-term memory (main session only)

Source: `~/repo/openclaw/src/agents/workspace.ts` lines 237-291, `loadWorkspaceBootstrapFiles()`

**Subagent sessions** only receive `AGENTS.md` + `TOOLS.md` (filtered by `SUBAGENT_BOOTSTRAP_ALLOWLIST`).

### Workspace Directory Resolution

Source: `~/repo/openclaw/src/agents/agent-scope.ts` lines 154-169, `resolveAgentWorkspaceDir()`

For each agent, the gateway resolves the workspace directory:
1. Agent-specific `workspace` config → use that path
2. If agent IS the default agent → use `agents.defaults.workspace`
3. If agent is NOT default → `~/.openclaw/workspace-{agentId}/`

Our agent "cleber" is not the default agent, so the gateway uses `~/.openclaw/workspace-cleber/` — NOT the configured `~/openclaw/` path.

### Template vs Custom Files

Source: `~/repo/openclaw/src/agents/workspace.ts` lines 125-198, `ensureAgentWorkspace()`

On first creation, the gateway populates the per-agent workspace from internal templates (`docs/reference/templates/`). Files are written using `writeFileIfMissing()` — existing files are never overwritten.

The templates are the official OpenClaw defaults, not our custom nix-managed content.

### Our Solution: Dual Deployment

The nix module deploys all workspace files to BOTH paths:
- `~/openclaw/` — the configured workspace (for reference/compatibility)
- `~/.openclaw/workspace-{agent}/` — where the gateway actually reads from

This is handled by the `openclaw.deployToBoth` helper in `config.nix`.

## File Categories

### Nix-Managed (read-only at runtime)

Deployed via nix to both workspace paths as symlinks to `/nix/store`:

| File | Purpose |
|------|---------|
| `AGENTS.md` | Operating instructions, tool patterns, boundaries |
| `SOUL.md` | Personality, autonomy, boundaries |
| `IDENTITY.md` | Name, emoji, vibe |
| `USER.md` | Human profile |
| `GRID.md` | Grid communication (on-demand reference, not injected) |
| `tts.json` | TTS engine and voice config |
| `rules/` | Development rules (not injected, read on-demand) |
| `skills/` | Skill definitions with SKILL.md files |
| `scripts/` | Shell/Python utility scripts |

### Agent-Managed (writable)

Created by the agent at runtime. NOT managed by nix — the gateway creates these from templates on first use:

| File | Purpose |
|------|---------|
| `TOOLS.md` | Runtime discoveries, learned tips |
| `HEARTBEAT.md` | Current heartbeat tasks |
| `MEMORY.md` | Curated long-term memory |
| `BOOTSTRAP.md` | First-run setup (deleted after use) |
| `memory/` | Daily logs and heartbeat state |
| `projects/` | Agent work directories |

## Key Design Decisions

### Why AGENTS.md is the single instruction file

Steps 1-4 of the refactoring research established:
- INSTRUCTIONS.md was 80% duplicate of AGENTS.md and never injected — deleted
- AI-TOOLS.md had critical tool patterns but was never injected — merged into AGENTS.md
- TOOLS-BASE.md was 100% duplicated in AI-TOOLS.md — deleted
- Community consensus (GitHub 2,500+ repo analysis): put everything in AGENTS.md with commands first

### Why dual deployment

The gateway's `resolveAgentWorkspaceDir()` uses `~/.openclaw/workspace-{id}` for non-default agents. Our configured `agents.defaults.workspace = "/home/zanoni/openclaw"` only applies to the default agent (which "cleber" is not). Rather than fighting the framework, we deploy to both paths.

### Why rules/ is kept separate

`rules/` is a Claude Code concept (`.claude/rules/`), not an OpenClaw concept. OpenClaw has no code that processes rules files or their frontmatter. They're deployed to the workspace as reference docs the bot can read on-demand.

### Content structure follows "commands first"

From GitHub's analysis and community research:
1. Context reference (what's injected)
2. Startup (minimal — just memory reads)
3. Tool patterns & commands (jq, bash, web research, TTS)
4. Workspace structure
5. Memory system
6. Safety & boundaries (Always/Ask/Never framework)
7. Dotfiles workflow
8. Session hygiene
9. Group chats
10. Heartbeats
11. Sub-agent delegation
12. Usage strategy
13. Common mistakes

### AGENTS.md sizing

Current: ~14KB after merging AI-TOOLS.md content. Well under OpenClaw's 20K `bootstrapMaxChars` truncation limit. If it grows past 20K, increase the config rather than splitting content across non-injected files.

## Advanced Features (Not Yet Enabled)

From step 3 research — config changes for `openclaw.json`, separate from workspace:

| Feature | Config | Status |
|---------|--------|--------|
| Memory flush before compaction | `compaction.memoryFlush.enabled: true` | Not enabled |
| Hybrid memory search (BM25+vector) | `memorySearch.enabled: true` | Needs embedding API key |
| BOOT.md startup automation | `hooks.internal.enabled: true` | Not enabled |
| Per-agent model/workspace overrides | `agents.list[].workspace` | Could configure cleber directly |

## References

- Strategy plan: `workspace-refactor-strategy-plan.md`
- Step 1 (internal audit): `workspace-refactoring-step-1.md`
- Step 2 (source cross-reference): `workspace-refactoring-step-2.md`
- Step 3 (advanced patterns): `workspace-refactoring-step-3.md`
- Step 4 (community research): `workspace-refactoring-step-4.md`
- Step 5 (implementation plan): `workspace-refactoring-step-5.md`
- OpenClaw source architecture: `openclaw-src.md`
