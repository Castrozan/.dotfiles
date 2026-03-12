---
name: hey-clever
description: Push-to-talk voice assistant with speech-to-text and TTS. Use when configuring the hey-clever voice keybind, debugging voice transcription, or troubleshooting the whisp-away to OpenClaw gateway pipeline.
---

<keybind_trap>
Hyprland keybind: SUPER ALT C. Uses bindd (on press) to start whisp-away recording and bindrd (on release) to trigger the hey-clever script. This bindd/bindrd distinction is critical — regular bind won't work for hold-to-record behavior.
</keybind_trap>

<flow>
Hold keybind to record, release to transcribe via whisp-away, send to gateway, play TTS response. The script handles the full pipeline — read it for implementation details.
</flow>
