---
name: avatar
description: "Control the VTuber avatar — speak with lip sync, change expressions, route audio to speakers or Meet. Use when making the avatar speak, changing emotions, or troubleshooting avatar issues."
---

# Avatar — VTuber Control

## Start / Stop

```bash
systemctl --user start avatar-control-server   # Start control server
systemctl --user stop avatar-control-server    # Stop
systemctl --user status avatar-control-server  # Check
curl -s http://localhost:8766/health           # Health check
```

Renderer (visual): `cd ~/openclaw/avatar/renderer && npm run dev` (serves on port 3000)

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

- **No audio in Meet**: Check `pactl list sinks short | grep AvatarMic`, use output `mic` or `both`
- **No audio in room**: Check output is `speakers` or `both`, check system volume
- **Speak hangs**: Must send `identify` before any other WebSocket command
- **Virtual camera not in Meet**: Restart Meet (Chrome enumerates devices at join)
- **Renderer won't start**: Run `npm install` in `~/openclaw/avatar/renderer/`
