---
name: hey-clever
description: Push-to-talk voice assistant. Uses whisp-away for transcription, sends to OpenClaw gateway, plays TTS response. Triggered via Hyprland keybind.
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
