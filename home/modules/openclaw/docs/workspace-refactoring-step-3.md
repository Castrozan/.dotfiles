# Step 3: Deeper OpenClaw Source Patterns

## Summary of Step 2 Findings

OpenClaw hardcodes 8 bootstrap files: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, BOOTSTRAP.md, MEMORY.md. Our custom files (INSTRUCTIONS.md, AI-TOOLS.md, TOOLS-BASE.md, GRID.md) are never injected. Worse, AGENTS.md tells the bot NOT to read AI-TOOLS.md because it claims it's "auto-injected" — so the bot has been flying blind on tool patterns.

## Advanced Features We're Not Using

### 1. BOOT.md — Gateway Startup Automation

When `hooks.internal.enabled = true`, OpenClaw executes `BOOT.md` as a silent agent turn on every gateway restart. The agent can use tools (including `message`) to send notifications, check system status, or initialize daily tasks.

**Relevance:** Could replace some startup logic currently crammed into HEARTBEAT.md. Morning briefings, service health checks, daily task initialization — all can run automatically on gateway start without waiting for a heartbeat poll.

**Config needed:**
```json5
{ hooks: { internal: { enabled: true } } }
```

### 2. Bootstrap Hooks — Dynamic Context Injection

`applyBootstrapHookOverrides()` in `src/agents/bootstrap-hooks.ts` allows hooks to mutate the bootstrap files array before injection. A hook can replace, modify, or add files based on session key, time, or external state.

**Relevance:** Instead of cramming everything into a static AGENTS.md, we could use a bootstrap hook to inject time-sensitive or channel-specific context. E.g., inject grid communication rules only for main sessions, or inject different tool patterns for night shift vs daytime.

**Assessment:** Interesting but over-engineering for now. Our merged AGENTS.md at ~14KB is well under the 20K limit. Revisit if AGENTS.md grows unwieldy.

### 3. Memory Search — Hybrid BM25 + Vector

OpenClaw supports semantic search over memory files via `memory_search` and `memory_get` tools. Hybrid mode combines vector similarity (paraphrases) with BM25 (exact tokens like error strings, env vars).

**Config:**
```json5
{
  agents: { defaults: {
    memorySearch: {
      enabled: true,
      provider: "openai",
      query: { hybrid: { enabled: true, vectorWeight: 0.7, textWeight: 0.3 } }
    }
  }}
}
```

**Relevance:** High. Instead of the bot reading through daily memory files manually at startup, it could search semantically. "What did I learn about polymarket?" would find relevant entries across all daily files. Also supports indexing session transcripts (`experimental.sessionMemory: true`) and extra paths.

**Assessment:** Should enable. Reduces startup cost (no need to read yesterday's full log) and improves memory recall quality. Requires an embedding provider API key.

### 4. Memory Flush — Auto-Save Before Compaction

When the session approaches context window limits, OpenClaw triggers a silent agent turn asking the bot to write durable memories before compaction destroys them.

**Config:**
```json5
{
  agents: { defaults: {
    compaction: {
      memoryFlush: {
        enabled: true,
        softThresholdTokens: 4000
      }
    }
  }}
}
```

**Relevance:** High. The bot currently loses context during long sessions without saving. Memory flush ensures important information survives compaction automatically, without relying on the bot remembering to write things down.

**Assessment:** Should enable. No workspace file changes needed — purely a config addition.

### 5. bootstrapMaxChars — Configurable Truncation Limit

Default is 20,000 chars per bootstrap file. Files exceeding this are truncated (70% head + 20% tail + marker).

**Current sizes:**
- AGENTS.md: 9,237 chars (OK)
- TOOLS.md: 3,098 chars (OK)
- After merging AI-TOOLS.md into AGENTS.md: ~14,020 chars (OK, under 20K)

**Assessment:** No change needed now. If AGENTS.md grows past 20K in the future, increase via config rather than splitting content across non-injected files.

### 6. Subagent Minimal Mode

Subagents receive ONLY `AGENTS.md` + `TOOLS.md`. All other bootstrap files are filtered out. System prompt uses `promptMode: "minimal"` — no skills list, no memory recall, no heartbeat instructions, no silent reply rules.

**Implication for our refactoring:**
- Everything a subagent needs to function must be in AGENTS.md or TOOLS.md
- Tool patterns (currently in AI-TOOLS.md) are critical for subagents — they need jq/yq, bash optimization, web research priority. Merging into AGENTS.md fixes this.
- Grid communication (GRID.md) is NOT needed by subagents — keeping it as a separate on-demand file is correct
- Sub-agent context rules (currently in AGENTS.md) are self-referential — subagents reading about how to spawn subagents they can't spawn. Harmless but wasteful.

### 7. Per-Agent Config

Each agent in `agents.list[]` can override: workspace, model, memory search, sandbox, tools, subagent settings, heartbeat config.

**Current state:** We use per-agent nix config for workspace content (template substitution with @agentName@ etc.) but the OpenClaw gateway config probably doesn't have per-agent overrides set up.

**Assessment:** Not a workspace refactoring concern, but worth reviewing the openclaw.json separately.

### 8. rules/ Directory — Not an OpenClaw Concept

Confirmed: `rules/` is purely a Claude Code convention. OpenClaw has zero code that reads, processes, or understands rules files or their frontmatter (alwaysApply, globs, etc.).

The files sit in the workspace and do nothing unless the bot manually reads them. Our AGENTS.md references "rules/core.md — core dev rules (auto-injected, alwaysApply)" — this is false. It's not auto-injected by OpenClaw.

**Options:**
1. Keep deploying rules/ as reference docs the bot CAN read on-demand
2. Merge critical rules into AGENTS.md (so they're actually seen)
3. Stop deploying them to the openclaw workspace

**Assessment:** Option 1 for now. The rules are shared with Claude Code via symlinks to ~/.claude/rules/ where they DO work. The openclaw workspace copies are redundant but harmless. Don't merge into AGENTS.md — it would bloat it. The bot can read them if instructed.

## Conclusions for the Refactoring

### What to do in the workspace files (step 5/6):

1. **Merge AI-TOOLS.md into AGENTS.md** — tool patterns are critical, currently invisible
2. **Delete INSTRUCTIONS.md** — 100% redundant zombie file
3. **Delete TOOLS-BASE.md** — content already in AI-TOOLS.md (which merges into AGENTS.md)
4. **Delete AI-TOOLS.md** — after merging into AGENTS.md
5. **Keep GRID.md** — on-demand reference for grid communication
6. **Fix AGENTS.md false claims** — remove AI-TOOLS.md, rules/core.md from "auto-injected" list
7. **Clean SOUL.md** — remove stale date stamp

### What to do in OpenClaw config (separate task, not this refactoring):

1. Enable memory flush (`compaction.memoryFlush.enabled: true`)
2. Enable memory search if embedding API available
3. Consider BOOT.md for startup automation
4. Review per-agent config for cleber/romario

### What NOT to do:

- Don't use bootstrap hooks for dynamic injection — over-engineering
- Don't increase bootstrapMaxChars — not needed at ~14KB
- Don't merge rules/ into AGENTS.md — too much bloat
- Don't try to make non-bootstrap files get injected — fight the framework

### Estimated final AGENTS.md size:

Current AGENTS.md: 9,237 chars
AI-TOOLS.md to merge (minus the "Base System Configuration" section already covered): ~3,800 chars
Total: ~13,037 chars (~65% of 20K limit, comfortable headroom)
