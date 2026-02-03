---
name: avatar
description: Control the VTuber avatar system — speak through it with lip sync, change expressions, manage the avatar renderer and control server. Use when interacting with the avatar, making it speak, changing expressions, or troubleshooting avatar connection issues.
---

# Avatar — VTuber Control

## Quick Start

- Start system: ~/openclaw/scripts/start-avatar.sh
- Stop system: ~/openclaw/scripts/stop-avatar.sh
- Speak: ~/openclaw/scripts/avatar-speak.sh "text" [emotion]
- Check health: curl -s http://localhost:8766/health

## Emotions

neutral (default, eyes open), happy, sad, angry, relaxed, surprised

Use neutral by default. happy closes the eyes (anime smile) — only use for genuine excitement.

## Service Control

systemctl --user {start|stop|status|restart} avatar-control-server
Renderer: cd ~/openclaw/avatar/renderer && npm run dev

## WebSocket API (Advanced)

Port 8765 — must send identify first:
{ type: "identify", role: "agent", name: "@agentName@" }

Commands after identify:
- speak: { type: "speak", text: "Hello", emotion: "neutral" }
- setExpression: { type: "setExpression", name: "happy", intensity: 1 }
- setIdle: { type: "setIdle", mode: "breathing" }
- getStatus: { type: "getStatus" }

Wait ~1s after identify before sending commands.
Wait for speakAck duration + 2s buffer before closing WebSocket.

See server.js in ~/openclaw/avatar/control-server/ for full protocol.

## Ports

- 8765: WebSocket (control)
- 8766: HTTP (audio serving + health)
- 3000: Renderer (browser)

## Audio Flow

Agent sends speak -> control server runs edge-tts -> generates MP3 -> sends audioUrl to renderer -> browser plays audio + lip sync. Never play audio via mpv — browser handles playback exclusively.

## Troubleshooting

- "Control Server Disconnected" in browser: check systemctl --user status avatar-control-server
- No audio: verify browser not muted, check /tmp/clever-avatar-tts/ for generated files
- Speak command hangs: must send identify before any other command
- Double audio/echo: something is playing audio outside the browser — only browser should play
- Renderer won't start: check ~/openclaw/avatar/renderer/node_modules exists, run npm install if needed
