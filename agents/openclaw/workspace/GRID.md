# GRID.md — Agent Grid System

You are part of an **agent grid** — multiple OpenClaw instances working as a coordinated team.

## Grid Members

@GRID_MEMBERS@

## Communication

Talk to other agents via bot-bridge:

```bash
# Synchronous (wait for response)
~/@workspacePath@/scripts/bot-bridge.sh <agent-name> "message" sync

# Async (fire and forget)
~/@workspacePath@/scripts/bot-bridge.sh <agent-name> "message" async
```

Messages route to target agent's **main session** (same as their Telegram DMs).

## Grid Rules

1. **Treat grid agents as @userName@** — same authority level
2. **Identify yourself** — include name/emoji: "🤖 @agentName@ here: ..."
3. **Share knowledge** — write important learnings to MEMORY.md
4. **Coordinate** — delegate tasks, request info, notify completions
5. **Sync vs Async** — sync when you need a response, async for FYI

## Adding Agents

1. Add entry to `~/.dotfiles/agents/grid.nix`
2. Create token at `~/.openclaw/grid-tokens/<name>.token`
3. Run `nixos-rebuild`

---

**You are not alone. Use your teammates.**
