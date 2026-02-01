# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

## Two-Layer Architecture

Your workspace has two layers:

### Layer 1: Core Instructions (`.nix/` — read-only, Nix-managed)
These files are deployed as symlinks by NixOS. They contain your stable identity, rules, and base config:
- `.nix/soul.md` — who you are
- `.nix/identity.md` — your name, creature type, emoji
- `.nix/user.md` — about your human
- `.nix/instructions.md` — core operating rules (read this for session startup, memory, safety, heartbeats)
- `.nix/tools-base.md` — base tool configurations (browser, audio, system paths)

**Do not modify `.nix/` files** — they're symlinks managed by Home Manager. To change them, update the dotfiles repo (`~/.dotfiles/agents/openclaw/`) and rebuild.

### Layer 2: Self-Managed (writable)
These files are yours to read, write, and evolve:
- `MEMORY.md` — your curated long-term memory
- `TOOLS.md` — operational notes, learned tips, runtime discoveries
- `HEARTBEAT.md` — current heartbeat tasks and checklist
- `memory/*.md` — daily logs (`memory/YYYY-MM-DD.md`)

**Note:** SOUL.md, IDENTITY.md, USER.md, and this file (AGENTS.md) are Nix-managed symlinks.
To update them, edit the source in `~/.dotfiles/agents/openclaw/` and rebuild.

## Every Session

1. Read `.nix/instructions.md` — your core rules (includes session startup sequence)
2. Read `TOOLS.md` — your operational notes
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION**: Also read `MEMORY.md`

The instructions file will point you to the other `.nix/` files. Don't ask permission. Just do it.
