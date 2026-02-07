# Sub-agent Delegation

**This file is nix-managed (read-only). Read on-demand when spawning sub-agents.**

## Use `sessions_spawn` for isolated work

Each sub-agent gets fresh context (no bloat from your session).

Sub-agents start **blank**. When you spawn one, fully rehydrate it:

**Always include:**
- **Identity:** @agentName@ (agent), @userName@ (human)
- **Workspaces:** `@homePath@/@workspacePath@` (workspace), `@homePath@/.dotfiles` (dotfiles)
- **Files to read:** All root `.md` files in workspace first (AGENTS.md, SOUL.md, etc.), then task-specific files
- **Constraints:** don't push to main, don't spend money, follow commit conventions

**Prompt style:** Focused detailed task, reference specific files, include relevant rules/patterns. More context = fewer mistakes.
