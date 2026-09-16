---
name: desktop
description: Automate desktop input, screenshots, clipboard, and media controls across Linux/Wayland and macOS. Use for non-browser GUI interaction or local media; keyboard and mouse are Linux/Wayland-only.
---

### Cross platform capability routing

For full, region, or active-window screenshots, read [screenshot](references/screenshot.md). For clipboard read, write,
or watch, read [clipboard](references/clipboard.md); watch is Linux-only. For playback and volume through MPRIS on Linux
or system audio and Music.app on macOS, read [media control](references/media-control.md).

### Linux wayland capability routing

For keyboard input through wtype, read [keyboard](references/keyboard.md). For mouse clicks, movement, scrolling, or
dragging through ydotool, read [mouse](references/mouse.md).

### Macos debugging routing

For macOS desktop traps that cost real debugging: window and application queries that report confidently wrong state,
accessibility under-reporting, Hammerspoon probe pitfalls, applications that rewrite their own settings, and the absence
of screen capture over SSH; read [knowledge](references/knowledge.md).
