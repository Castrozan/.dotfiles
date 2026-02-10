---
name: avatar
description: "Control the VTuber avatar — speak with lip sync, change expressions, route audio to speakers or Meet. Use when making the avatar speak, changing emotions, or troubleshooting avatar issues."
---

# Avatar — VTuber Control

## Hey-Bot Voice Conversation
When the avatar is active and hey-bot is running, maintain conversation through voice:

**Unbreakable Principles:**
- Create a cron job (every 20s) to check hey-bot transcriptions and respond via avatar-speak.sh
- Listen to hey-bot transcriptions, respond via avatar-speak.sh
- Do NOT use Telegram when avatar conversation is active
- **ALWAYS** use sub-agents for background work, keep main thread for conversation

**Monitor transcriptions:**
```bash
# Check latest transcriptions
tail -20 ~/.local/share/hey-bot/transcriptions/current.log

# Respond to user voice
avatar-speak.sh "Your response here" neutral speakers
```

**Microphone setup:**
- System default: laptop internal mic (`alsa_input.pci-0000_05_00.6.HiFi__Mic1__source`)
- Avatar does NOT change system default mic automatically
- `AvatarMicSource` is available but not default — select in Meet/calls when needed
- To restore real mic: `pactl set-default-source alsa_input.pci-0000_05_00.6.HiFi__Mic1__source`

## Start / Stop

`start-avatar.sh` is the single entry point — it starts all 5 services in order:

1. **Virtual audio** — AvatarSpeaker + AvatarMic PulseAudio sinks
2. **Control server** — WebSocket (8765) + HTTP (8766) via systemd
3. **Renderer** — ChatVRM on http://localhost:3000
4. **Virtual camera** — CDP screencast from renderer to /dev/video10
5. **Health checks** — verifies all services

```bash
start-avatar.sh          # Start everything
stop-avatar.sh           # Stop everything
```

To see the renderer visually: `pw open http://localhost:3000 --headed`

## Speaking

```bash
avatar-speak.sh "Hello world"                    # Default: neutral, speakers
avatar-speak.sh "I'm excited!" happy             # With emotion
avatar-speak.sh "Hello Meet!" neutral mic        # To virtual mic (calls)
avatar-speak.sh "Everyone hears" happy both      # Speakers + mic
```

### Multi-Segment (emotion changes mid-speech)

```bash
avatar-speak-multi.sh \
  "happy:Hi, I'm Clever!" \
  "neutral:I work with Lucas on daily tasks." \
  "surprised:Wait, what's happening?" \
  "relaxed:Let me think about this."
```

Format: `"emotion:text"` — segments play sequentially with emotion transitions.

Append `mic` or `both` as last arg to change output target.

## Emotions

`neutral` (default), `happy`, `sad`, `angry`, `relaxed`, `surprised`

Use `neutral` by default. `happy` closes eyes (anime smile) — only for genuine excitement.

## Audio Output

| Target | Where audio plays | Use case |
|--------|------------------|----------|
| `speakers` | Default system sink | People in room hear it |
| `mic` | AvatarMic virtual sink | People in Meet/calls hear it |
| `both` | Both simultaneously | Room + call |

## WebSocket API (Advanced)

Port 8765. Must send identify first, wait ~1s before commands:

```json
{ "type": "identify", "role": "agent", "name": "@agentName@" }
{ "type": "speak", "text": "Hello", "emotion": "neutral", "output": "mic" }
{ "type": "setExpression", "name": "happy", "intensity": 1 }
{ "type": "setIdle", "mode": "breathing" }
{ "type": "getStatus" }
```

Wait for `speakAck` duration + 2s buffer before closing WebSocket.

## Ports

| Port | Service |
|------|---------|
| 8765 | WebSocket control |
| 8766 | HTTP (audio serving + health) |
| 3000 | Renderer (browser) |
| /dev/video10 | Virtual camera |

## Troubleshooting

- **Duplicate voice heard**: Browser renderer plays audio for lip-sync while mpv plays to speakers; expected behavior
- **No audio in Meet**: Check `pactl list sinks short | grep AvatarMic`, use output `mic` or `both`
- **No audio in room**: Check output is `speakers` or `both`, check system volume
- **Speak hangs**: Must send `identify` before any other WebSocket command
- **Virtual camera not in Meet**: Restart Meet (Chrome enumerates devices at join)
- **Renderer won't start**: Run `npm install` in `~/openclaw/avatar/renderer/`
