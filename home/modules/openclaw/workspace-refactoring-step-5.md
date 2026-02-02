# Step 5: Final Consolidated Implementation Plan

## Summary

Synthesizing steps 1-4 into exact file changes. The core problem: 4 of our 8 nix-managed workspace files are never injected by OpenClaw, and AGENTS.md falsely claims they are — so the bot has been operating without tool patterns, with duplicate instructions, and with conflicting startup sequences.

## Files to Delete (3)

### 1. `INSTRUCTIONS.md` (11.9KB)
- 80% duplicate of AGENTS.md, never injected
- Only 2 unique lines worth keeping: "avoid the triple-tap" and default heartbeat prompt text
- Those 2 items merge into new AGENTS.md

### 2. `TOOLS-BASE.md` (778B)
- 100% duplicated in AI-TOOLS.md's "Base System Configuration" section
- Stale (says "small model" for Whisper, AI-TOOLS.md correctly says "tiny")

### 3. `AI-TOOLS.md` (4.8KB)
- Never injected by OpenClaw — bot thinks it's in context but it's not
- All content merges into AGENTS.md so it's actually visible

## Files to Modify (2)

### 4. `AGENTS.md` — Full Rewrite

Merge AI-TOOLS.md content in. Restructure following community "commands first" pattern from GitHub's 2,500-repo analysis. Add Always/Ask/Never boundary framework. Fix false auto-injection claims. Add session hygiene. Add "avoid the triple-tap". Add default heartbeat prompt text. Note nix-managed read-only constraint.

**New structure (following step 4 recommendation):**
1. What's in your context (corrected — only actual bootstrap files)
2. Every session (minimal startup)
3. Tool patterns & commands (merged from AI-TOOLS.md — commands early!)
4. Workspace structure (corrected file list)
5. Memory system
6. Safety & boundaries (Always/Ask/Never framework)
7. Dotfiles workflow
8. Session hygiene (new — subagent isolation, output containment)
9. Group chats & communication (with "avoid the triple-tap")
10. Heartbeats (with default prompt text)
11. Sub-agent delegation
12. Usage strategy
13. Common mistakes (corrected — no false AI-TOOLS.md reference)

**Estimated size:** ~13-14KB (under 20K truncation limit)

### 5. `SOUL.md` — Remove Stale Date Stamp

Remove line 64: `*Updated: 2026-01-30 — Added initiative & autonomy section per Lucas's request*`

## Files to Keep Unchanged (2)

- `IDENTITY.md` (822B) — properly injected, no changes needed
- `USER.md` (1.5KB) — properly injected, no changes needed
- `GRID.md` (3.7KB) — kept as on-demand reference file, not claimed as injected

## Nix Changes

None. `workspace.nix` uses `builtins.readDir` on `agents/openclaw/workspace/` — deleting source files automatically stops deployment.

## Implementation Order

1. Write new AGENTS.md (full rewrite with merged content)
2. Remove stale date from SOUL.md
3. Delete INSTRUCTIONS.md, TOOLS-BASE.md, AI-TOOLS.md
4. Stage all changes
5. Dry-run rebuild
6. Apply rebuild
7. Verify: `ls ~/openclaw/*.md` shows only AGENTS.md, GRID.md, IDENTITY.md, SOUL.md, USER.md
8. Commit

## Result

- 8 nix-managed files → 5 nix-managed files
- ~35KB → ~18KB (~49% reduction)
- All critical content in auto-injected AGENTS.md
- No false claims about injection
- Bot finally receives tool patterns (jq, bash, web research, TTS, system commands)
- Subagents also receive tool patterns (AGENTS.md is in subagent allowlist)
- Clear Always/Ask/Never boundaries
- Session hygiene guidance for token savings
