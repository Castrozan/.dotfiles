---
name: avatar
description: "Control the VTuber avatar — speak with lip sync, change expressions, route audio to speakers or Meet."
---

# Avatar — VTuber Control

## Quick Start

```bash
start-avatar.sh          # Start all services
stop-avatar.sh           # Stop everything
```

## Speaking

```bash
avatar-speak.sh "Hello world"                    # neutral, speakers
avatar-speak.sh "I'm excited!" happy             # with emotion
avatar-speak.sh "Hello Meet!" neutral mic        # virtual mic (calls)
avatar-speak.sh "Everyone hears" happy both      # speakers + mic
```

### Multi-Segment

```bash
avatar-speak-multi.sh \
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

When avatar is active with hey-bot daemon:
- Monitor transcriptions: `tail -20 ~/.local/share/hey-bot/transcriptions/current.log`
- Respond via `avatar-speak.sh`, not Telegram
- Mic picks up speaker output → hey-bot Rule (6) auto-ignores self-generated speech
- System default mic stays as laptop internal mic (not AvatarMicSource)

## Ports

| Port | Service |
|------|---------|
| 8765 | WebSocket control |
| 8766 | HTTP (audio + health) |
| 3000 | Renderer |
| /dev/video10 | Virtual camera |

## Troubleshooting

- **No audio in Meet**: `pactl list sinks short | grep AvatarMic`, use output `mic`
- **Speak hangs**: Control server must be running (`curl localhost:8766/health`)
- **Virtual camera not in Meet**: Restart Meet (Chrome enumerates at join)
- **Renderer won't start**: `npm install` in `~/openclaw/avatar/renderer/`
