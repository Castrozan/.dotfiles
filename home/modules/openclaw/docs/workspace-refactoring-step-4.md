# Step 4: Community Research — How to Build a Powerful OpenClaw Workspace

## Sources

### Already in our night shift research (Jan 31 / Feb 1):
- arxiv 2601.20404: AGENTS.md reduces tokens by 16.6%, runtime by 28.6%
- OpenClaw issues #1594 (token burns), #4561 (multi-agent scaling)
- agentsmd.io, builder.io, JetBrains, Elementor/Medium optimization guides
- OpenAI Codex AGENTS.md guide

### New from this research:
- [GitHub Blog: How to write a great agents.md (2,500+ repos analyzed)](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [APIYI: OpenClaw token cost optimization guide](https://help.apiyi.com/en/openclaw-token-cost-optimization-guide-en.html)
- [Matt Pocock on X: Bad AGENTS.md files cost tokens](https://x.com/mattpocockuk/status/2012906065856270504)
- [Dan Mac on X: AGENTS.md is the MOST IMPORTANT file](https://x.com/daniel_mac8/status/1924461757881524418)
- OpenClaw official docs: agent-workspace, context, system-prompt
- [OpenClaw security patterns (Medium)](https://alirezarezvani.medium.com/agents-md-top-safety-rules-that-your-ai-assistant-openclaw-need-d50f95ce9e7c)

---

## Key Patterns from Community

### 1. AGENTS.md is THE file — make it count

From GitHub's analysis of 2,500+ repos, the most effective AGENTS.md files share 6 core areas:
1. **Commands** (with flags, early in the file)
2. **Testing practices**
3. **Project file structure**
4. **Code style with examples**
5. **Git workflow**
6. **Clear boundaries** (Always/Ask/Never framework)

**Our gap:** Our AGENTS.md focuses on operational behavior (memory, heartbeats, group chats, usage strategy) but misses tool commands and project structure. The tool patterns are in AI-TOOLS.md which is NEVER INJECTED.

### 2. Commands first, theory later

GitHub Blog: "Put commands early — agents reference them frequently."

**Our gap:** Our most actionable content (jq/yq commands, bash optimization, web research priority, TTS flow, system commands) is buried in AI-TOOLS.md. The bot never sees it. The stuff the bot DOES see (AGENTS.md) is mostly philosophy and process, not actionable commands.

### 3. Token efficiency is the #1 community concern

APIYI guide: "Continuous context window accumulation is responsible for 40-50% of token consumption." Users report $150/month reduced to $35 with optimization.

Key strategies from community:
- **Session reset after independent tasks** (biggest single savings)
- **Tool output isolation** — heavy commands in subagent sessions
- **Cache warmth** — heartbeat intervals < cache TTL
- **Model routing** — cheap models for simple tasks
- **Context window capping** — 50-100K instead of full 400K

**What this means for us:** Our AGENTS.md should teach the bot these patterns. Currently it says "use Opus for complex, Sonnet for routine" but doesn't explain session isolation or output containment.

### 4. Three-tier boundary framework works

GitHub Blog's highest-performing pattern:
- **Always do:** Specific permitted actions
- **Ask first:** Major changes requiring approval
- **Never do:** Absolute prohibitions

**Our current approach:** We have Safety + External vs Internal sections that roughly map to this, but they're vague. "Don't run destructive commands" vs "Never: rm -rf without explicit permission, push to main without rebuild, spend money without asking."

### 5. Living document pattern

Multiple sources: AGENTS.md should evolve. Tell the agent "update AGENTS.md with what you learned."

**Our constraint:** AGENTS.md is a nix symlink — read-only. The bot can't update it. This conflicts with the community pattern. However, our TOOLS.md IS writable and serves this purpose. The bot should be told explicitly: "AGENTS.md is read-only (nix-managed). Write runtime discoveries to TOOLS.md."

### 6. Subagent context isolation is critical

JetBrains + OpenClaw source: Subagents should have minimal context. OpenClaw already does this — only AGENTS.md + TOOLS.md for subagents. This means:
- Everything a subagent needs must be in those 2 files
- Currently subagents get our AGENTS.md (operational behavior) but NOT AI-TOOLS.md (tool patterns) — they're flying blind on HOW to use tools

### 7. Memory search over manual file reading

OpenClaw supports hybrid BM25+vector memory search. Community consensus: searching beats reading full files at startup. The bot should search for relevant context on-demand rather than loading everything upfront.

---

## What Other OpenClaw Users Do (from community)

### Workspace simplicity
Most users keep the default 7 bootstrap files + memory/. Extra files are rare. Our 8+ custom non-bootstrap files are unusual and arguably counterproductive since they're never injected.

### AGENTS.md as the master document
The official template puts EVERYTHING operational into AGENTS.md: memory rules, safety, group chats, heartbeats, tool guidance, startup sequence. Users who split instructions across multiple files often report confusion and token waste.

### TOOLS.md as the runtime scratchpad
Community uses TOOLS.md for:
- Environment-specific notes (SSH hosts, camera names, API endpoints)
- Learned tips and gotchas
- Runtime configuration that changes between sessions

This matches our current TOOLS.md usage pattern.

### Session hygiene
Power users emphasize:
- Reset sessions after heavy diagnostic work
- Use subagents for anything that produces large output
- Keep heartbeat intervals tuned to cache TTL (prevents cold cache penalty)
- Set `contextTokens` lower than default to trigger compaction earlier

---

## Synthesis: What This Means for Our Refactoring

### Confirmed by community research:

1. **Merge AI-TOOLS.md into AGENTS.md** — tool commands must be in the injected file. This is the single biggest improvement. The bot has been without tool guidance for every session.

2. **Delete INSTRUCTIONS.md** — AGENTS.md IS the instructions file. Having a separate one is an anti-pattern that no other OpenClaw user follows.

3. **Delete TOOLS-BASE.md** — base config belongs in the injected AGENTS.md or TOOLS.md.

4. **Put commands early in AGENTS.md** — jq/yq, bash optimization, web research, TTS should appear BEFORE philosophical guidance about memory and heartbeats.

5. **Add explicit boundaries** — convert vague Safety section to Always/Ask/Never framework.

6. **Note the read-only constraint** — tell the bot AGENTS.md is nix-managed, use TOOLS.md for discoveries.

### New insights from community:

7. **Add session hygiene guidance** — teach the bot about session resets, output containment in subagents, context management. This saves real money.

8. **Enable memory search** — reduces startup cost from reading full daily logs to semantic search on-demand.

9. **Heartbeat + cache TTL alignment** — set heartbeat interval slightly below cache TTL for warm-cache cost savings.

10. **Consider making AGENTS.md writable** — the community pattern of "living documents" is powerful. Counter-argument: nix-management prevents drift and ensures consistency across agents. Decision: keep nix-managed, but make TOOLS.md the explicit evolution surface.

### Structure recommendation for merged AGENTS.md:

Following the "commands first" principle from GitHub's 2,500-repo analysis:

```
1. What's in your context (quick reference)
2. Every session (startup — just memory reads)
3. Tool patterns & commands (jq, bash, web search, TTS, system)
4. Workspace structure
5. Memory system
6. Safety & boundaries (Always/Ask/Never)
7. Dotfiles workflow
8. Session hygiene (subagent isolation, output containment)
9. Group chats & communication
10. Heartbeats
11. Sub-agent delegation
12. Usage strategy
13. Common mistakes
```

This puts actionable tool content (section 3) early — where agents reference it most — and pushes behavioral philosophy (heartbeats, group chats) later.
