---
name: desktop
description: Control native desktop apps, keyboard, mouse, screenshots, clipboard, and media on macOS and Linux/Wayland. Use for non-browser GUI interaction or local media.
---

### Native app computer use

On macOS, use the shared `desktop-computer-use` MCP: start with `doctor`, inspect controls through `get_ui_tree`, and
follow its tool descriptions for targeting and screenshot coordinates. The terminal or agent host needs macOS
Accessibility and Screen Recording grants; installation alone cannot grant them.

On Hyprland, run the `hypruse` CLI from the shell; `hypruse VERB --help` is the ground truth for flags. Start with
`hypruse desktop` and act on window addresses: `hypr` and `launch` for windows, `click_ui NAME --window ADDR` for a
named control, `--window ADDR` on every `keyboard` call. Agents share the `marks` numbering, so run `marks` right before
`click_ui --mark N`. A capture prints an image path and its geometry; read that file to see it. Exit 3 is a final
refusal to report, never to route around. Verify the visible result after every action.

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
