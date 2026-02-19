---
name: hey-clever
description: Push-to-talk voice assistant with speech-to-text and TTS. Use when configuring the hey-clever voice keybind, debugging voice transcription, or troubleshooting the whisp-away to OpenClaw gateway pipeline.
---

<flow>
Hold keybind to record, release to transcribe via whisp-away, send to gateway, play TTS response. Hyprland keybind: SUPER ALT C — bindd starts whisp-away recording, bindrd triggers the hey-clever script on release.
</flow>

<script>
scripts/hey-clever.sh stops whisp-away recording, reads transcription from clipboard, sends to gateway, plays TTS via edge-tts + mpv.
</script>
