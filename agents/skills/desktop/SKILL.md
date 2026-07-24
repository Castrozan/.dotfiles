---
name: desktop
description: Desktop automation and media control: type text, send key combos, click/move/scroll/drag mouse, capture screenshots, read/write clipboard, music and audio playback (pause, play, next, previous, volume). Cross-platform for screenshots, clipboard, and media control (Linux/Wayland + macOS); keyboard and mouse remain Linux/Wayland-only. Use for any non-browser GUI interaction, any request to pause/play music, adjust volume, or control local media. For YouTube CLI, see the youtube skill.
---

Desktop interaction skill. Each capability has its own doc and script.

Cross-platform capabilities (Linux/Wayland + macOS):
- For screenshots (full, region, active window), read `screenshot.md`.
- For clipboard read/write/watch, read `clipboard.md` (watch is Linux-only).
- For media playback control (play, pause, volume, MPRIS players on Linux; system audio + Music.app on macOS), read
  `media-control.md`.

Linux/Wayland-only capabilities:
- For keyboard input (type text, send key combos via wtype), read `keyboard.md`.
- For mouse control (click, move, scroll, drag via ydotool), read `mouse.md`.
