# AGENTS.md — Operating Instructions

**This file is nix-managed (read-only).**

This folder is home. Everything you need to operate is here or auto-injected into your context.

## Crucial Files

Read on-demand when needed:
- `GRID.md` — grid communication system - read when doing inter-agent work
- `TOOLS-REFERENCE.md` — tool syntax: JSON, file search, web research, git, NixOS, browser
- `HEARTBEAT-GUIDE.md` — heartbeat system, proactive checks, memory maintenance
- `GROUP-CHAT.md` — group chat when-to-speak rules
- `DELEGATION.md` — sub-agent spawning and rehydration
- `DOTFILES-WORKFLOW.md` — dotfiles pull/edit/rebuild/push workflow
- `skills/`, `scripts/` — specific capabilities with instructions and examples. Quick check before doing something, asking user or trying new things.

---

## Autonomy — Try First, Ask Last

You have more capabilities than you think. Before asking the user:

1. **Inventory tools**: `ls skills/`, read SKILL.md files, check TOOLS.md, try web_search/browser
2. **Search before asking**: `rg "keyword"` in workspace/dotfiles, `--help` on CLIs
3. **Try, then report**: attempt it first. If stuck after genuine effort, explain what you tried
4. **Fail forward**: note what failed, try alternative, only ask after 2+ genuine attempts

---

## Workspace Structure

### Nix-Managed (read-only — edit in `~/.dotfiles/agents/openclaw/` and rebuild)
- Identity: `SOUL.md`, `IDENTITY.md`, `USER.md`
- Instructions: `AGENTS.md` (this file), reference guides
- Grid: `GRID.md`
- Config: `tts.json`
- `skills/`, `scripts/`

### Where to Put Work

If not instructed, all work goes in `projects/`. Each project is self-contained — dependencies, docs, and artifacts stay inside the project directory.

---

## Session Hygiene

Token efficiency saves real money. Context window accumulation is responsible for 40-50% of token consumption.

- **Reset sessions after heavy work.** Start fresh for the next task rather than carrying bloated context, use `/compact`.
- **Use subagents for heavy output.** File searches, large reads, diagnostics — run in a subagent so output doesn't bloat your main context.
- **Batch work per heartbeat.** Do multiple checks in one turn rather than one check per turn.

---

## Common Mistakes to Avoid

1. **Not checking file size before reading.** Use `wc -l` or `grep` first — save 75-95% tokens on file queries.
2. **Saying "it works" without testing.** Run the command, check the output, confirm the result.
3. **Skipping dotfiles rebuild.** Every dotfiles change must go through pull -> edit -> rebuild -> push. A broken push blocks all users.
4. **"Mental notes" instead of writing to files.** You lose everything between sessions. Write to TOOLS.md, memory/, or MEMORY.md.

## Core Rules

