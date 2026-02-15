---
name: hey-clever
description: Push-to-talk voice assistant with speech-to-text and TTS. Use when configuring the hey-clever voice keybind, debugging voice transcription, or troubleshooting the whisp-away to OpenClaw gateway pipeline.
---

# Hey Clever -- Push-to-Talk Voice Assistant

Press keybind to record, release to transcribe (whisp-away), send to gateway, and play TTS response.

## Keybind (Hyprland)

Hold `SUPER ALT, C` to record, release to process:

```
bindd = SUPER ALT, C, Hey Clever start, exec, whisp-away start
bindrd = SUPER ALT, C, Hey Clever stop, exec, ~/openclaw/skills/hey-clever/scripts/hey-clever.sh
```

## Script

`scripts/hey-clever.sh` — stops whisp-away recording, reads transcription from clipboard, sends to gateway, plays TTS via edge-tts + mpv.
