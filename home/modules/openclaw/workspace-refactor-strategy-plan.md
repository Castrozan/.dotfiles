# OpenClaw Workspace Refactoring Strategy

## Goal

Lean down the workspace instruction files to align with OpenClaw's actual architecture, eliminate redundancy, and make the bots more efficient (fewer tokens wasted, clearer guidance, no conflicting instructions).

## Steps

### Step 1: Internal Audit (DONE)
File: `workspace-refactoring-step-1.md`

Cataloged all 8 nix-managed workspace files, identified overlaps between AGENTS.md/INSTRUCTIONS.md (80% duplicate), and TOOLS-BASE.md/AI-TOOLS.md (100% duplicate). Mapped each section and decided keep/drop/merge.

### Step 2: Cross-Reference with OpenClaw Source (DONE)
File: `workspace-refactoring-step-2.md`

Read the OpenClaw source code (`~/repo/openclaw`) to understand exactly how workspace files are loaded, which files are auto-injected, and what the official templates look like. Key finding: OpenClaw hardcodes 8 bootstrap files. Our INSTRUCTIONS.md, AI-TOOLS.md, TOOLS-BASE.md, GRID.md are never injected. AGENTS.md falsely claims AI-TOOLS.md is injected, so the bot skips reading it — losing all tool patterns.

### Step 3: Read OpenClaw Source for Advanced Patterns (DONE)
File: `workspace-refactoring-step-3.md`

Explored BOOT.md automation, bootstrap hooks, memory search (hybrid BM25+vector), memory flush before compaction, bootstrapMaxChars config, subagent minimal mode, per-agent overrides, and rules/ directory. Confirmed rules/ is not an OpenClaw concept. Key conclusions: merge AI-TOOLS.md into AGENTS.md (~13KB total, under 20K limit), keep GRID.md as on-demand reference, enable memory flush and memory search in config separately.

### Step 4: Community Research
Search the internet for how other OpenClaw/AI-agent users structure their workspaces. Look at:
- OpenClaw Discord/community posts
- GitHub repos with openclaw workspace configs
- X/Twitter posts about agent workspace optimization
- Blog posts about prompt engineering for persistent agents
Extract patterns and ideas that could improve our setup.

### Step 5: Final Consolidated Plan
Synthesize steps 1-4 into a single implementation plan with exact file changes. Account for:
- OpenClaw's actual bootstrap file list
- Community best practices
- Our specific needs (multi-agent grid, nix-managed, template substitution)

### Step 6: Implementation
Execute the plan: edit dotfiles, rebuild, verify, commit.

### Step 7: Testing
Restart the bot, verify correct files are injected via `/context list`, confirm no regressions.
