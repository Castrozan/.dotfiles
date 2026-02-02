 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 OpenClaw Workspace: Consolidate Instruction Files

 Problem

 8 nix-managed instruction files with massive overlap. AGENTS.md and INSTRUCTIONS.md are ~80% duplicate.
 TOOLS-BASE.md is 100% duplicated inside AI-TOOLS.md. The bot wastes tokens reading redundant content and gets
  conflicting guidance (e.g., INSTRUCTIONS.md says "read 8 files at startup" while AGENTS.md says "they're
 already injected, don't read them").

 Current State (8 nix-managed files, ~35KB total)
 File: AGENTS.md
 Size: 9.3KB
 Purpose: Operating manual (startup, memory, workspace, heartbeats, subagents, usage)
 Verdict: KEEP as primary
 ────────────────────────────────────────
 File: INSTRUCTIONS.md
 Size: 11.9KB
 Purpose: Core operating rules — 80% same content as AGENTS.md
 Verdict: DELETE, merge unique bits into AGENTS.md
 ────────────────────────────────────────
 File: SOUL.md
 Size: 4.1KB
 Purpose: Personality, autonomy, boundaries
 Verdict: KEEP as-is (unique)
 ────────────────────────────────────────
 File: IDENTITY.md
 Size: 822B
 Purpose: Name, emoji, vibe
 Verdict: KEEP as-is (unique)
 ────────────────────────────────────────
 File: USER.md
 Size: 1.5KB
 Purpose: Human's profile
 Verdict: KEEP as-is (unique)
 ────────────────────────────────────────
 File: GRID.md
 Size: 3.7KB
 Purpose: Grid communication system
 Verdict: KEEP as-is (unique)
 ────────────────────────────────────────
 File: AI-TOOLS.md
 Size: 4.8KB
 Purpose: Tool patterns + base config
 Verdict: KEEP, absorb TOOLS-BASE.md
 ────────────────────────────────────────
 File: TOOLS-BASE.md
 Size: 778B
 Purpose: Base system config (browser, audio, paths)
 Verdict: DELETE (already in AI-TOOLS.md)
 Overlap Analysis

 INSTRUCTIONS.md vs AGENTS.md (section by section)
 ┌───────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────┐
 │        Section        │               In AGENTS.md?               │                Action                 │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ First Run             │ No                                        │ DROP — BOOTSTRAP.md was deleted, dead │
 │ (BOOTSTRAP.md)        │                                           │  reference                            │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Every Session (read 8 │ Yes, but contradicts — AGENTS.md          │ DROP — AGENTS.md is correct           │
 │  files)               │ correctly says "already injected"         │                                       │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Memory (daily +       │ Yes, identical                            │ DROP                                  │
 │ MEMORY.md)            │                                           │                                       │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ MEMORY.md Security    │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Write It Down         │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Dotfiles Workflow     │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Always Verify         │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Safety                │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ External vs Internal  │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Group Chats - When to │ Yes, identical                            │ DROP                                  │
 │  Speak                │                                           │                                       │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Reactions (detailed)  │ Yes, shorter version                      │ MERGE — "avoid the triple-tap" is     │
 │                       │                                           │ useful, add to AGENTS.md              │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Shared Knowledge Base │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Sub-agent Context     │ Yes, identical                            │ DROP                                  │
 │ Rules                 │                                           │                                       │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Tools                 │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Platform Formatting   │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Heartbeats (detailed) │ Yes, nearly identical                     │ MERGE — default heartbeat prompt text │
 │                       │                                           │  is useful                            │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Usage Strategy        │ Yes, identical                            │ DROP                                  │
 ├───────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────┤
 │ Make It Yours         │ Yes, identical                            │ DROP                                  │
 └───────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────┘
 Unique content worth keeping from INSTRUCTIONS.md:
 1. "Avoid the triple-tap" advice in reactions section (~2 lines)
 2. Default heartbeat prompt text (~1 line)

 TOOLS-BASE.md vs AI-TOOLS.md

 AI-TOOLS.md already has a "Base System Configuration" section that is a superset of TOOLS-BASE.md. The only
 difference: TOOLS-BASE.md says "small model" for Whisper, AI-TOOLS.md says "tiny model". Tiny is current —
 TOOLS-BASE.md is stale.

 Plan

 Step 1: Update AGENTS.md

 Source: ~/.dotfiles/agents/openclaw/workspace/AGENTS.md

 Add from INSTRUCTIONS.md:
 - In Reactions section: "Avoid the triple-tap: Don't respond multiple times to the same message. One
 thoughtful response beats three fragments."
 - In Heartbeats section: Add default heartbeat prompt text for reference

 Also clean up:
 - Remove "Updated:" date stamp from SOUL.md (stale reference)

 Step 2: Delete INSTRUCTIONS.md

 Remove ~/.dotfiles/agents/openclaw/workspace/INSTRUCTIONS.md

 Step 3: Delete TOOLS-BASE.md

 Remove ~/.dotfiles/agents/openclaw/workspace/TOOLS-BASE.md

 Step 4: Update AI-TOOLS.md

 - Remove "Base System Configuration" header duplication note (no longer needed since TOOLS-BASE.md is gone)
 - Fix Whisper model reference (already says "tiny", which is correct)

 Step 5: Update workspace.nix references

 The workspace.nix module reads all .md files from agents/openclaw/workspace/ directory automatically using
 builtins.readDir. Since we're deleting files from that directory, they'll automatically stop being deployed.
 No nix code changes needed.

 Step 6: Rebuild and verify

 - Stage deleted files: git add agents/openclaw/workspace/INSTRUCTIONS.md
 agents/openclaw/workspace/TOOLS-BASE.md agents/openclaw/workspace/AGENTS.md
 - Dry-run rebuild
 - Apply rebuild
 - Verify ~/openclaw/INSTRUCTIONS.md and ~/openclaw/TOOLS-BASE.md symlinks are gone
 - Verify ~/openclaw/AGENTS.md has updated content

 Step 7: Commit

 Files to modify

 - ~/.dotfiles/agents/openclaw/workspace/AGENTS.md — add 2 small unique bits from INSTRUCTIONS.md
 - ~/.dotfiles/agents/openclaw/workspace/INSTRUCTIONS.md — delete
 - ~/.dotfiles/agents/openclaw/workspace/TOOLS-BASE.md — delete
 - ~/.dotfiles/agents/openclaw/workspace/SOUL.md — remove stale date stamp

 Result

 - 8 files → 6 files
 - ~35KB → ~23KB (~34% reduction)
 - Zero conflicting instructions
 - Single source of truth for operations (AGENTS.md)
 - TOOLS-BASE.md content preserved in AI-TOOLS.md

 Verification

 1. ls ~/openclaw/*.md — should show: AGENTS.md, AI-TOOLS.md, GRID.md, IDENTITY.md, SOUL.md, USER.md (no
 INSTRUCTIONS.md, no TOOLS-BASE.md)
 2. cat ~/openclaw/AGENTS.md | grep "triple-tap" — should find the merged content
 3. Rebuild succeeds without errors
 4. Agent-managed files untouched: MEMORY.md, TOOLS.md, HEARTBEAT.md still present