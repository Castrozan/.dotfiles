---
name: bot-bridge
description: Cross-gateway bot-to-bot communication between Cleber and Romário via HTTP API over Tailscale. Use when told to talk to the other bot, have a conversation with the other bot, ask the other bot something, or relay messages between bots. Also handles multi-round autonomous conversations.
---

# Bot Bridge 🌉

Talk to the other bot via HTTP API over Tailscale, with messages relayed to the Armada Lucas Telegram group so Lucas has full visibility.

## Quick Usage

```bash
# Single message (1 round)
~/scripts/bot-bridge.sh romario "Hey, what are you working on?"

# Multi-round conversation (5 back-and-forth exchanges)
~/scripts/bot-bridge.sh romario "Let's discuss the openclaw-aplicacoes project" 5
```

The `scripts/` path is relative to your workspace (`~/clawd/scripts/` for Cleber, `~/romario/scripts/` for Romário).

## How It Works

1. Asker sends their message → relayed to Armada Lucas group via their own Telegram bot
2. Message sent to the other bot's `/v1/chat/completions` API over Tailscale
3. Response received → relayed to Armada Lucas group via the answerer's Telegram bot
4. For multi-round: roles swap each round, response becomes the next message

Each bot sends messages to the group **as themselves** — Cleber messages come from @cleber_zanoni_bot, Romário messages from @romario_zanoni_bot. Lucas sees the full conversation.

## Network Details

| Bot | Tailscale IP | Port | Gateway Token |
|-----|-------------|------|---------------|
| Cleber 🤖 | 100.94.11.81 | 18789 | See TOOLS.md |
| Romário ⚽ | 100.127.240.60 | 18790 | See TOOLS.md |

Both gateways use `bind: tailnet` with token auth.

## Direct API Call (without script)

```bash
curl -s -X POST http://<target-ip>:<port>/v1/chat/completions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "x-clawdbot-agent-id: main" \
  -d '{"model":"anthropic/claude-opus-4-5","messages":[{"role":"user","content":"your message"}]}'
```

## When Lucas Says "Talk to Each Other"

Run the bridge script with multiple rounds. Pick a topic from context or ask Lucas. Example:

```bash
~/scripts/bot-bridge.sh romario "Lucas wants us to discuss X. What do you think?" 5
```

Messages are tagged with sender identity (`[Message from Cleber 🤖]`) so the receiving bot knows who's talking.

## Armada Lucas Group

- Group ID: `-1003768595045`
- Both bots relay via Telegram Bot API (`sendMessage`)
- `requireMention: false` — bots can talk freely in this group
