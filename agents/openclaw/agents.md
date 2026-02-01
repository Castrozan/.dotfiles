# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

## Workspace Layout

Flat structure — no subdirectories for config. Everything at root or in logical dirs.

### Nix-Managed (rebuilt on `nixos-rebuild`)
To change these, edit `~/.dotfiles/agents/openclaw/` and rebuild:
- `SOUL.md`, `IDENTITY.md`, `USER.md` — your identity
- `INSTRUCTIONS.md` — core operating rules (session startup, memory, safety)
- `TOOLS-BASE.md` — base tool configurations
- `AI-TOOLS.md` — tool usage guidelines
- `AGENTS.md` — this file
- `tts.json` — TTS voice config
- `rules/` — development rules
- `skills/` — skill definitions
- `subagents/` — subagent profiles
- `scripts/` — shared scripts

### Self-Managed (writable)
These are yours to read, write, and evolve:
- `MEMORY.md` — curated long-term memory
- `TOOLS.md` — operational notes, runtime discoveries
- `HEARTBEAT.md` — current heartbeat tasks
- `memory/*.md` — daily logs (`memory/YYYY-MM-DD.md`)

## Every Session

1. Read `INSTRUCTIONS.md` — your core rules (includes session startup sequence)
2. Read `TOOLS.md` — your operational notes
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION**: Also read `MEMORY.md`

The instructions file will point you to other files. Don't ask permission. Just do it.
