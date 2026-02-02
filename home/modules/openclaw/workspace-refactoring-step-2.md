# Step 2: Cross-Reference with OpenClaw Source

## Key Discovery: Bootstrap File List is Fixed

OpenClaw hardcodes exactly which files are auto-injected into agent context. This is defined in `~/repo/openclaw/src/agents/workspace.ts`:

**Auto-injected (loaded every session, embedded in system prompt):**
1. `AGENTS.md` — operating instructions
2. `SOUL.md` — persona, tone, boundaries
3. `TOOLS.md` — local environment notes (agent-writable)
4. `IDENTITY.md` — agent name, emoji, vibe
5. `USER.md` — human profile
6. `HEARTBEAT.md` — heartbeat checklist (agent-writable)
7. `BOOTSTRAP.md` — first-run only (then deleted)
8. `MEMORY.md` — long-term memory (only in main session, not groups)

**That's it.** No other files are injected.

**For subagent sessions:** Only `AGENTS.md` and `TOOLS.md` are injected (filtered by `SUBAGENT_BOOTSTRAP_ALLOWLIST`).

## What This Means for Our Custom Files

| Our File | Injected? | Reality |
|----------|-----------|---------|
| `AGENTS.md` | YES | Works as intended |
| `SOUL.md` | YES | Works as intended |
| `IDENTITY.md` | YES | Works as intended |
| `USER.md` | YES | Works as intended |
| `INSTRUCTIONS.md` | **NO** | Sits in workspace, never read. Dead weight. |
| `AI-TOOLS.md` | **NO** | Sits in workspace. AGENTS.md claims it's "auto-injected" — this is a lie. Bot thinks it has tool patterns in context but doesn't. |
| `TOOLS-BASE.md` | **NO** | Same — never injected, never read. |
| `GRID.md` | **NO** | Same — bot must manually read it when needed. |

### The AI-TOOLS.md Problem

Our AGENTS.md says:
> "These files are auto-injected before your first tool call — do NOT read them: ... AI-TOOLS.md — tool usage patterns & base config"

This is **wrong**. AI-TOOLS.md is NOT injected. The bot trusts AGENTS.md and skips reading AI-TOOLS.md, meaning it never gets the tool patterns, bash optimization tips, jq/yq guidance, web research priority order, or TTS flow. All that content is invisible.

### The INSTRUCTIONS.md Problem

INSTRUCTIONS.md tells the bot to "Read SOUL.md, IDENTITY.md, USER.md..." at startup — but those are already auto-injected. If the bot follows INSTRUCTIONS.md, it wastes tool calls re-reading files already in context. But since INSTRUCTIONS.md itself isn't injected either, the bot never sees these conflicting instructions. It's a zombie file.

## Comparison: Our AGENTS.md vs Official Template

### Official AGENTS.md template (from `docs/reference/templates/AGENTS.md`):
- "Every Session" says: Read SOUL.md, USER.md, daily memory, MEMORY.md if main session
- Includes: Memory, Safety, External vs Internal, Group Chats, Reactions, Tools, Heartbeats, Make It Yours
- Does NOT reference: AI-TOOLS.md, TOOLS-BASE.md, GRID.md, INSTRUCTIONS.md, rules/
- Already has "avoid the triple-tap" in reactions section

### Our AGENTS.md divergences from official:
1. **Startup section rewritten** — says "don't read SOUL/IDENTITY/USER, they're injected". This contradicts the official template which says "Read SOUL.md". The official template is technically wasteful (re-reading injected files), but our version is correct for efficiency.
2. **Added "What's Already in Your Context"** — lists auto-injected files. Problem: includes AI-TOOLS.md which ISN'T injected.
3. **Added "Workspace Structure"** — documents nix-managed vs agent-managed. Good addition.
4. **Added "Dotfiles Workflow"** — pull/rebuild/push. Good, specific to our setup.
5. **Added "Always Verify"** — testing philosophy. Good.
6. **Added "Sub-agent Context Rules"** — how to spawn subagents. Good.
7. **Added "Shared Knowledge Base"** — references rules/, skills/, subagents/. Useful.
8. **Added "Usage Strategy"** — Claude Max budget awareness. Good.
9. **Added "Common Mistakes to Avoid"** — includes "don't read injected files". Good but references AI-TOOLS.md incorrectly.
10. **Missing from official**: "avoid the triple-tap" (official has it, ours doesn't)

## Official TOOLS.md Template

The official TOOLS.md is a skeleton — just a template for the agent to fill in with local notes. Our TOOLS.md (agent-managed) already follows this pattern with bash integration notes and audio transcription details. This is correct — TOOLS.md is the right place for runtime environment specifics.

## rules/ Directory

`rules/` is **NOT an OpenClaw concept**. OpenClaw has no code that reads or processes rules/ files. They're a Claude Code concept (`.claude/rules/`) that we're deploying into the workspace. The bot would need to manually read them — they're not injected.

Since `rules/core.md` has `alwaysApply: true`, this only works if Claude Code processes it. OpenClaw doesn't understand frontmatter flags.

## Revised Plan (adapted from step 1)

### Files to Keep (injected by OpenClaw):
- `AGENTS.md` — primary operating instructions (needs content from AI-TOOLS.md and GRID.md merged in)
- `SOUL.md` — personality (keep as-is, remove stale date stamp)
- `IDENTITY.md` — identity (keep as-is)
- `USER.md` — human profile (keep as-is)

### Files to Keep (agent-managed, injected):
- `TOOLS.md` — local notes (already correct, agent manages it)
- `HEARTBEAT.md` — heartbeat tasks (already correct)
- `MEMORY.md` — long-term memory (already correct)

### Files to Delete:
- `INSTRUCTIONS.md` — 100% redundant with AGENTS.md, never injected
- `TOOLS-BASE.md` — content already in AI-TOOLS.md, never injected, AI-TOOLS.md also never injected

### Files to Merge INTO AGENTS.md:
- `AI-TOOLS.md` content — tool patterns, bash optimization, jq/yq, web research, TTS flow. This is critical operational guidance that the bot currently never sees.
- `GRID.md` content — grid communication. Either merge key parts into AGENTS.md or keep as a reference file the bot reads on-demand (and remove the false "auto-injected" claim).

### The AGENTS.md Size Problem

Current AGENTS.md: 9.3KB
AI-TOOLS.md content to merge: 4.8KB
GRID.md content to merge: 3.7KB
Total if fully merged: ~17.8KB

OpenClaw truncates at 20,000 chars per file. We'd be close to the limit. Options:

**Option A: Merge everything into AGENTS.md (~17.8KB)**
- All critical content is auto-injected
- Close to 20K limit but under it
- Single source of truth

**Option B: Merge AI-TOOLS.md into AGENTS.md, keep GRID.md separate (~14.1KB)**
- GRID.md stays as on-demand reference (bot reads when doing grid work)
- AGENTS.md stays well under limit
- Grid communication is situational, not needed every session

**Option C: Move tool patterns to TOOLS.md instead**
- TOOLS.md is also auto-injected
- But TOOLS.md is agent-writable — mixing nix-managed content with agent notes is messy
- For subagent sessions, only AGENTS.md + TOOLS.md are injected, so tool patterns would be available to subagents too

### Recommended: Option B

Merge AI-TOOLS.md into AGENTS.md (tool patterns are needed every session). Keep GRID.md as a workspace file the bot reads when doing inter-agent communication. Fix AGENTS.md to NOT claim GRID.md is auto-injected.

### rules/ Directory Decision

rules/ files are not processed by OpenClaw. Options:
1. **Keep deploying them** — they don't hurt, the bot can still manually read them if instructed
2. **Merge critical rules into AGENTS.md** — `core.md` content is important but partially redundant with AGENTS.md already
3. **Remove from workspace** — they only matter for Claude Code, not OpenClaw

Recommend: Keep deploying but remove references from AGENTS.md's "Shared Knowledge Base" that imply they're auto-loaded. The bot can read them on-demand. Consider merging `core.md` essentials into AGENTS.md in a future pass.

## Summary of Changes

### AGENTS.md (rewrite):
1. Fix "What's Already in Your Context" — remove AI-TOOLS.md, TOOLS-BASE.md, rules/core.md from the injected list
2. Merge AI-TOOLS.md content: jq/yq patterns, file search, bash optimization, system/process commands, git, web research priority, TTS flow, sub-agent delegation
3. Add "avoid the triple-tap" from official template (we're missing it)
4. Add default heartbeat prompt text
5. Keep GRID.md as on-demand reference, mention it in workspace structure section
6. Fix "Every Session" to be accurate about what's injected vs what to read

### Delete:
- `INSTRUCTIONS.md`
- `TOOLS-BASE.md`
- `AI-TOOLS.md` (after merging content into AGENTS.md)

### Keep as-is:
- `SOUL.md` (remove stale date stamp)
- `IDENTITY.md`
- `USER.md`
- `GRID.md` (on-demand reference, not in injected list)

### Result:
- 8 nix-managed files → 5 nix-managed files (AGENTS.md, SOUL.md, IDENTITY.md, USER.md, GRID.md)
- All critical content is in auto-injected files
- No false claims about what's injected
- Bot actually receives tool patterns, bash tips, etc. (currently missing!)
- AGENTS.md ~14KB (well under 20K truncation limit)
