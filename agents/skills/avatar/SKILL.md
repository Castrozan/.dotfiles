---
name: avatar
description: "Control the VTuber avatar — speak with lip sync, change expressions, route audio to speakers or Meet."
---

# Avatar — VTuber Control

Scripts are at `@homePath@/@workspacePath@/skills/avatar/scripts/`.

## Quick Start

```bash
@homePath@/@workspacePath@/skills/avatar/scripts/start-avatar.sh    # Start all services (opens visible browser)
@homePath@/@workspacePath@/skills/avatar/scripts/stop-avatar.sh      # Stop everything
```

## Speaking

```bash
@homePath@/@workspacePath@/skills/avatar/scripts/avatar-speak.sh "Hello world"                    # neutral, speakers
@homePath@/@workspacePath@/skills/avatar/scripts/avatar-speak.sh "I'm excited!" happy             # with emotion
@homePath@/@workspacePath@/skills/avatar/scripts/avatar-speak.sh "Hello Meet!" neutral mic        # virtual mic (calls)
@homePath@/@workspacePath@/skills/avatar/scripts/avatar-speak.sh "Everyone hears" happy both      # speakers + mic
```

### Multi-Segment

```bash
@homePath@/@workspacePath@/skills/avatar/scripts/avatar-speak-multi.sh \
  "happy:Hi, I'm Clever!" \
  "neutral:Let me think about this."
```

Format: `"emotion:text"` — plays sequentially. Append `mic` or `both` as last arg.

## Emotions

`neutral` (default), `happy`, `sad`, `angry`, `relaxed`, `surprised`

## Audio Output

| Target | Where | Use case |
|--------|-------|----------|
| `speakers` | System sink | Room audio |
| `mic` | AvatarMic virtual sink | Meet/calls |
| `both` | Both | Room + call |

## Voice Conversation Mode

When avatar is active with hey-bot daemon, set up a cron job to poll transcription logs and respond through the avatar.

### Cron Setup (mandatory when voice mode is active)

Create this cron job using the `cron` tool:

```json
{
  "name": "hey-bot-monitor",
  "schedule": {"kind": "every", "everyMs": 30000},
  "sessionTarget": "main",
  "payload": {
    "kind": "systemEvent",
    "text": "hey-bot-monitor: check transcription logs now"
  },
  "enabled": true
}
```

### When you receive the `hey-bot-monitor` system event, you MUST:

1. **Read the log**: `tail -15 ~/.local/share/hey-bot/transcriptions/current.log`
2. **Filter out noise**: Ignore entries that are:
   - Nonsensical (`1 %`, repeated numbers, dots, garbled text)
   - Your own TTS being re-transcribed (sounds like an AI assistant response)
   - Older than 60 seconds (already stale)
3. **Respond to genuine speech**: If there's human speech directed at you (mentions jarvis/clever/hey bot, or direct questions/commands), respond via:
   ```bash
   avatar-speak.sh "your response" emotion speakers
   ```
4. **If nothing new**: respond with NO_REPLY — do NOT skip reading the log

### Key rules
- Respond via `avatar-speak.sh`, not Telegram
- Mic picks up speaker output → hey-bot Rule (6) auto-ignores self-generated speech
- System default mic stays as laptop internal mic (not AvatarMicSource)
- Keep responses concise (2-3 sentences max) for natural conversation

## Ports

| Port | Service |
|------|---------|
| 8765 | WebSocket control |
| 8766 | HTTP (audio + health) |
| 3000 | Renderer (browser) |
| /dev/video* | Virtual camera (auto-detected) |

## Troubleshooting

- **Can't see avatar**: Browser may be headless — `start-avatar.sh` opens with `--headed`
- **No audio in Meet**: `pactl list sinks short | grep AvatarMic`, use output `mic`
- **Speak hangs**: Control server must be running (`curl localhost:8766/health`)
- **Virtual camera not in Meet**: Restart Meet (Chrome enumerates at join)
- **Renderer won't start**: `npm install` in `@homePath@/@workspacePath@/skills/avatar/renderer/`
