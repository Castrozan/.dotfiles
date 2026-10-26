---
name: desktop
description: Control native desktop apps, keyboard, mouse, screenshots, clipboard, and media on macOS and Linux/Wayland. Use for non-browser GUI interaction or local media.
---

### Native app computer use

Use the shared `desktop-computer-use` MCP for native app interaction. On macOS, start with `doctor` and inspect controls
through `get_ui_tree`; on Hyprland, start with `desktop` and inspect controls through `ui`. Follow the server's tool
descriptions for targeting and screenshot coordinates, and verify the visible result after an action. macOS requires
Accessibility and Screen Recording grants for the terminal or agent host; installation alone cannot grant them.

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
